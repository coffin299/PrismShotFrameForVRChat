# SPDX-License-Identifier: Apache-2.0
"""RGB-D 画像の目印、分解、結合。"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# 各チャンネルの許容差。JPEG や色空間のずれを吸収する。
MARKER_TOLERANCE = 24
# 目印の先頭色。ASCII の P, S, F。
PSF = (80, 83, 70)
# 目印の末尾色。先頭の並びを逆にした対。
REVERSE = (70, 83, 80)
# 近い距離を書いた区画の B。
NEAR_TAG = 170
# 遠い距離を書いた区画の B。
FAR_TAG = 85


@dataclass
class RgbdImage:
    """分解した色、深度、撮影時の距離。"""

    color: np.ndarray
    depth: np.ndarray
    near_m: float
    far_m: float


def encode_depth(depth: np.ndarray) -> np.ndarray:
    """近いほど白い 0〜1 の深度を、R と G の 16bit にする。"""
    # 範囲外を切り、16bit の整数へ量子化する。
    clipped = np.clip(depth, 0.0, 1.0)
    value = np.rint(clipped * 65535.0).astype(np.uint16)
    # 上位と下位を別チャンネルに分ける。
    high = ((value >> 8) & 255).astype(np.uint8)
    low = (value & 255).astype(np.uint8)
    encoded = np.zeros(depth.shape + (3,), dtype=np.uint8)
    encoded[:, :, 0] = high
    encoded[:, :, 1] = low
    return encoded


def decode_depth(encoded: np.ndarray) -> np.ndarray:
    """R と G から 0〜1 の深度を戻す。"""
    high = encoded[:, :, 0].astype(np.uint16)
    low = encoded[:, :, 1].astype(np.uint16)
    value = (high << 8) | low
    return value.astype(np.float32) / 65535.0


def pack_rgbd(
    color: np.ndarray,
    depth: np.ndarray,
    near_m: float,
    far_m: float,
    step: int = 1,
) -> np.ndarray:
    """色と深度を左右に並べ、下端へ目印を書く。"""
    if color.shape[:2] != depth.shape[:2]:
        raise ValueError("色と深度の大きさが違います")
    # 左が色、右が深度。
    encoded = encode_depth(depth)
    packed = np.concatenate([color[:, :, :3], encoded], axis=1)
    _stamp_marker(packed, near_m, far_m, step)
    return packed


def is_rgbd(image: np.ndarray) -> bool:
    """目印があれば RGB-D とみなす。"""
    return _extract_card(image) is not None


def split_rgbd(image: np.ndarray) -> RgbdImage:
    """RGB-D を色、深度、距離範囲に分ける。"""
    found = _extract_card(image)
    if found is None:
        raise ValueError("RGB-D の目印がありません")
    card, near_m, far_m = found
    width = card.shape[1]
    # 奇数幅は右端を落として左右を同じ幅にする。
    if width % 2 != 0:
        card = card[:, : width - 1]
        width -= 1
    half = width // 2
    color = np.ascontiguousarray(card[:, :half])
    depth = decode_depth(card[:, half:])
    return RgbdImage(color=color, depth=depth, near_m=near_m, far_m=far_m)


def _split_u16(value: int) -> tuple[int, int]:
    """メートルの 100 倍を、上位バイトと下位バイトに分ける。"""
    limited = int(np.clip(int(round(value)), 0, 65535))
    return (limited >> 8) & 255, limited & 255


def _join_u16(high: int, low: int) -> int:
    """2バイトを 16bit 整数に戻す。"""
    return ((int(high) & 255) << 8) | (int(low) & 255)


def _stamp_marker(
    image: np.ndarray,
    near_m: float,
    far_m: float,
    step: int,
) -> None:
    """下端の左と、四隅の短い対を塗る。"""
    height, width, _ = image.shape
    if step < 1 or height < step or width < step * 6:
        return
    near_high, near_low = _split_u16(int(round(near_m * 100.0)))
    far_high, far_low = _split_u16(int(round(far_m * 100.0)))
    cells = (
        PSF,
        (near_high, near_low, NEAR_TAG),
        (far_high, far_low, FAR_TAG),
        REVERSE,
    )
    bottom = height - step
    # 4区画を左から同じ大きさで塗る。
    for index, color in enumerate(cells):
        left = index * step
        image[bottom : bottom + step, left : left + step] = color
    _stamp_pair(image, 0, 0, step)
    _stamp_pair(image, width - 2 * step, 0, step)
    _stamp_pair(image, width - 2 * step, bottom, step)


def _stamp_pair(image: np.ndarray, x: int, y: int, step: int) -> None:
    """隅の2区画に、先頭色と末尾色を塗る。"""
    height, width, _ = image.shape
    if x < 0 or y < 0 or x + 2 * step > width or y + step > height:
        return
    image[y : y + step, x : x + step] = PSF
    image[y : y + step, x + step : x + 2 * step] = REVERSE


def _close(pixel: np.ndarray, expected: tuple[int, int, int], tol: int) -> bool:
    """1ピクセルが期待色の許容差内か。"""
    return all(abs(int(pixel[channel]) - expected[channel]) <= tol for channel in range(3))


def _color_run(row: np.ndarray, x: int, expected: tuple[int, int, int], tol: int) -> int:
    """同じ色が何ピクセル続くかを数える。"""
    width = row.shape[0]
    length = 0
    while x + length < width and length < 64 and _close(row[x + length], expected, tol):
        length += 1
    return length


def _tag_run(row: np.ndarray, x: int, blue: int, tol: int) -> tuple[int, int, int]:
    """B がタグと一致し、R と G が一定の区画の長さと値を返す。"""
    width = row.shape[0]
    if x >= width:
        return 0, 0, 0
    high = int(row[x, 0])
    low = int(row[x, 1])
    length = 0
    while x + length < width and length < 64:
        pixel = row[x + length]
        # タグの B から外れたら区画の終わり。
        if abs(int(pixel[2]) - blue) > tol:
            break
        # 距離のバイトは区画内で同じである必要がある。
        if abs(int(pixel[0]) - high) > tol or abs(int(pixel[1]) - low) > tol:
            break
        length += 1
    return length, high, low


def _marker_at(image: np.ndarray, x: int, y: int, tol: int = MARKER_TOLERANCE) -> tuple[float, float] | None:
    """その位置から4区画が揃っていれば、近い距離と遠い距離を返す。"""
    height, width, _ = image.shape
    if y < 0 or y >= height or x < 0 or x >= width:
        return None
    row = image[y]
    first = _color_run(row, x, PSF, tol)
    if first < 1:
        return None
    second, near_high, near_low = _tag_run(row, x + first, NEAR_TAG, tol)
    third, far_high, far_low = _tag_run(row, x + first + second, FAR_TAG, tol)
    fourth = _color_run(row, x + first + second + third, REVERSE, tol)
    lengths = (first, second, third, fourth)
    # 4区画がすべて存在し、太さがほぼ同じであること。
    if min(lengths) < 1 or max(lengths) - min(lengths) > 2:
        return None
    near_m = _join_u16(near_high, near_low) / 100.0
    far_m = _join_u16(far_high, far_low) / 100.0
    return near_m, far_m


def _candidate_points(image: np.ndarray, tol: int = MARKER_TOLERANCE) -> list[tuple[int, int]]:
    """先頭色に近いピクセルだけを候補にする。"""
    red = image[:, :, 0].astype(np.int16)
    green = image[:, :, 1].astype(np.int16)
    blue = image[:, :, 2].astype(np.int16)
    mask = (
        (np.abs(red - PSF[0]) <= tol)
        & (np.abs(green - PSF[1]) <= tol)
        & (np.abs(blue - PSF[2]) <= tol)
    )
    rows, cols = np.nonzero(mask)
    # 写真全体を検証しすぎないよう、候補は先頭から限る。
    points = list(zip(cols.tolist(), rows.tolist()))
    return points[:48]


def _crop_from_marker(image: np.ndarray, x: int, y: int) -> np.ndarray | None:
    """目印を札の左下とみなし、上端にも先頭色がある最大の 2:1 を切り出す。"""
    height, width, _ = image.shape
    max_height = min(y + 1, (width - x) // 2)
    # 大きい方から試し、最初に隅が一致した範囲を採用する。
    for card_height in range(max_height, 7, -1):
        card_width = card_height * 2
        top = y - card_height + 1
        if top < 0 or x + card_width > width:
            continue
        if _close(image[top, x], PSF, MARKER_TOLERANCE):
            return np.ascontiguousarray(image[top : y + 1, x : x + card_width])
    return None


def _extract_card(
    image: np.ndarray,
) -> tuple[np.ndarray, float, float] | None:
    """画像から RGB-D の札と距離範囲を取り出す。"""
    if image.ndim != 3 or image.shape[2] < 3:
        return None
    rgb = image[:, :, :3]
    height = rgb.shape[0]
    # 下が画像の下端なら、ファイル全体が札。
    direct = _marker_at(rgb, 0, height - 1)
    if direct is not None:
        return rgb, direct[0], direct[1]
    # 上下が逆でも読めるようにする。
    flipped = np.ascontiguousarray(np.flipud(rgb))
    flipped_marker = _marker_at(flipped, 0, flipped.shape[0] - 1)
    if flipped_marker is not None:
        return flipped, flipped_marker[0], flipped_marker[1]
    # 画面いっぱいでない写真は、目印の位置から札を探す。
    for x, y in _candidate_points(rgb):
        found = _marker_at(rgb, x, y)
        if found is None:
            continue
        cropped = _crop_from_marker(rgb, x, y)
        if cropped is not None:
            return cropped, found[0], found[1]
    return None
