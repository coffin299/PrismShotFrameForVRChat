# SPDX-License-Identifier: Apache-2.0
"""キルトの名前、並び、大きさ。"""

import numpy as np

from prismshot.views.quilt import build_quilt, preset_grid, quilt_filename


def test_filename_and_preset():
    """例のファイル名と、縦長・横長の初期グリッド。"""
    assert quilt_filename("photo", 8, 6, 0.75) == "photo_qs8x6a0.75.png"
    assert preset_grid(3, 4) == (8, 6)
    assert preset_grid(16, 9) == (11, 6)


def test_quilt_order_and_resolution():
    """視点0は左下、最後は右上。大きさはタイル×枚数。"""
    columns, rows = 8, 6
    tile = 4
    views = []
    for index in range(columns * rows):
        views.append(np.full((tile, tile, 3), index, dtype=np.uint8))
    quilt = build_quilt(views, columns, rows)
    assert quilt.shape == (tile * rows, tile * columns, 3)
    assert int(quilt[-1, 0, 0]) == 0
    assert int(quilt[0, -1, 0]) == columns * rows - 1
