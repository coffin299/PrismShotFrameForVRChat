# SPDX-License-Identifier: Apache-2.0
"""深度に応じた横ずらしと、穴埋め。"""

from __future__ import annotations

import numpy as np


def view_sides(count: int) -> np.ndarray:
    """左端の視点を +1、右端の視点を -1 にする。"""
    if count < 1:
        raise ValueError("視点数は 1 以上です")
    if count == 1:
        return np.zeros(1, dtype=np.float32)
    # 手前は左端の視点で右へ、右端の視点で左へ動く。
    return np.linspace(1.0, -1.0, count, dtype=np.float32)


def synthesize_views(
    color: np.ndarray,
    depth: np.ndarray,
    view_count: int,
    max_disparity: float,
    focus: float,
    quality: str = "simple",
) -> list[np.ndarray]:
    """各視点の画像を作る。近い画素ほど大きくずれる。"""
    if color.shape[:2] != depth.shape[:2]:
        raise ValueError("色と深度の大きさが違います")
    views = []
    for side in view_sides(view_count):
        views.append(
            _shift_view(
                color[:, :, :3],
                depth.astype(np.float32),
                float(side),
                float(max_disparity),
                float(focus),
                quality,
            )
        )
    return views


def _shift_view(
    color: np.ndarray,
    depth: np.ndarray,
    side: float,
    max_disparity: float,
    focus: float,
    quality: str,
) -> np.ndarray:
    """1視点分を、奥から描いて手前が上書きする順で作る。"""
    height, width, _ = color.shape
    source_x = np.broadcast_to(np.arange(width), (height, width))
    source_y = np.broadcast_to(np.arange(height)[:, None], (height, width))
    # ピントの深度では変位が 0。近いほど絶対値が大きい。
    shift = (depth - focus) * max_disparity * side
    dest_x = np.rint(source_x + shift).astype(np.int32)
    inside = (dest_x >= 0) & (dest_x < width)
    ys = source_y[inside]
    xs = source_x[inside]
    dx = dest_x[inside]
    ds = depth[inside]
    # 同じ行き先では、後から書く近い画素を残す。
    order = np.argsort(ds, kind="stable")
    ys = ys[order]
    xs = xs[order]
    dx = dx[order]
    ds = ds[order]
    output = np.zeros((height, width, 3), dtype=np.uint8)
    out_depth = np.full((height, width), -1.0, dtype=np.float32)
    written = np.zeros((height, width), dtype=bool)
    output[ys, dx] = color[ys, xs]
    out_depth[ys, dx] = ds
    written[ys, dx] = True
    fill_holes(output, out_depth, written, color, quality)
    return output


def fill_holes(
    color: np.ndarray,
    depth: np.ndarray,
    written: np.ndarray,
    source: np.ndarray,
    quality: str,
) -> None:
    """空いた画素を、より遠い隣接から埋める。"""
    passes = 4 if quality == "high" else 1
    for _ in range(passes):
        if bool(np.all(written)):
            break
        # 高品質版は色が離れた隣を拒否し、残った穴は次の周回で埋める。
        _fill_pass(color, depth, written, source, quality, final=False)
    if quality == "high" and not bool(np.all(written)):
        _fill_pass(color, depth, written, source, "simple", final=True)


def _fill_pass(
    color: np.ndarray,
    depth: np.ndarray,
    written: np.ndarray,
    source: np.ndarray,
    quality: str,
    final: bool,
) -> None:
    """左右の最も近い有効画素のうち、条件に合う方を穴へコピーする。"""
    height, width = written.shape
    for y in range(height):
        valid = written[y]
        if not np.any(valid) or np.all(valid):
            continue
        xs = np.arange(width)
        # 左方向の最近傍は、インデックスの累積最大で求まる。
        left = np.maximum.accumulate(np.where(valid, xs, -1))
        right_source = np.where(valid, xs, width)
        right = np.minimum.accumulate(right_source[::-1])[::-1]
        holes = ~valid
        left_index = left[holes]
        right_index = right[holes]
        has_left = left_index >= 0
        has_right = right_index < width
        left_clip = np.clip(left_index, 0, width - 1)
        right_clip = np.clip(right_index, 0, width - 1)
        left_depth = np.where(has_left, depth[y, left_clip], np.float32(2.0))
        right_depth = np.where(has_right, depth[y, right_clip], np.float32(2.0))
        if quality == "high" and not final:
            origin = source[y, holes]
            left_color = color[y, left_clip]
            right_color = color[y, right_clip]
            left_diff = np.max(
                np.abs(left_color.astype(np.int16) - origin.astype(np.int16)),
                axis=1,
            )
            right_diff = np.max(
                np.abs(right_color.astype(np.int16) - origin.astype(np.int16)),
                axis=1,
            )
            # 元の色から離れた隣は、この周回では使わない。
            left_depth = np.where(has_left & (left_diff <= 48), left_depth, np.float32(2.0))
            right_depth = np.where(has_right & (right_diff <= 48), right_depth, np.float32(2.0))
        pick_left = left_depth <= right_depth
        usable = np.minimum(left_depth, right_depth) < 1.5
        hole_index = np.flatnonzero(holes)
        chosen = np.where(pick_left, left_clip, right_clip)
        use = hole_index[usable]
        source_x = chosen[usable]
        picked = color[y, source_x].copy()
        picked_depth = depth[y, source_x].copy()
        color[y, use] = picked
        depth[y, use] = picked_depth
        written[y, use] = True
