# SPDX-License-Identifier: Apache-2.0
"""キルトの配置とファイル名。"""

from __future__ import annotations

import numpy as np


def format_aspect(aspect: float) -> str:
    """縦横比を、末尾の余分な 0 を除いた文字列にする。"""
    text = f"{aspect:.4f}".rstrip("0").rstrip(".")
    return text if text else "0"


def quilt_filename(stem: str, columns: int, rows: int, aspect: float) -> str:
    """キルトのファイル名を作る。"""
    return f"{stem}_qs{columns}x{rows}a{format_aspect(aspect)}.png"


def preset_grid(width: int, height: int) -> tuple[int, int]:
    """縦長は 8x6、横長は 11x6。"""
    if height >= width:
        return 8, 6
    return 11, 6


def build_quilt(views: list[np.ndarray], columns: int, rows: int) -> np.ndarray:
    """視点0を左下、最後の視点を右上に並べる。"""
    count = columns * rows
    if len(views) != count:
        raise ValueError("視点の枚数が列×行と一致しません")
    tile_h, tile_w = views[0].shape[:2]
    canvas = np.zeros((tile_h * rows, tile_w * columns, 3), dtype=np.uint8)
    for index, view in enumerate(views):
        if view.shape[0] != tile_h or view.shape[1] != tile_w:
            raise ValueError("視点の大きさが揃っていません")
        # 横位置は左から。縦位置は下の行が視点の若い番号。
        column = index % columns
        row_from_bottom = index // columns
        top = (rows - 1 - row_from_bottom) * tile_h
        left = column * tile_w
        canvas[top : top + tile_h, left : left + tile_w] = view[:, :, :3]
    return canvas
