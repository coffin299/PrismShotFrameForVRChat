# SPDX-License-Identifier: Apache-2.0
"""視差の向きと穴埋め。"""

import numpy as np

from prismshot.views.shift import fill_holes, synthesize_views


def test_near_shifts_more_than_far():
    """手前の点は、奥の点より大きく横へ動く。"""
    color = np.zeros((32, 80, 3), dtype=np.uint8)
    depth = np.zeros((32, 80), dtype=np.float32)
    color[16, 10] = (0, 255, 0)
    depth[16, 10] = 0.0
    color[16, 40] = (255, 0, 0)
    depth[16, 40] = 1.0
    left = synthesize_views(color, depth, 2, 10.0, 0.0, "simple")[0]
    red_x = int(np.argmax(left[16, :, 0]))
    green_x = int(np.argmax(left[16, :, 1]))
    assert abs(red_x - 40) > abs(green_x - 10)


def test_simple_fill_picks_farther():
    """単純な穴埋めは、より遠い隣を採用する。"""
    color = np.zeros((1, 5, 3), dtype=np.uint8)
    source = np.zeros((1, 5, 3), dtype=np.uint8)
    color[0, 1] = (255, 0, 0)
    color[0, 3] = (0, 0, 255)
    source[0, 2] = (255, 0, 0)
    depth = np.array([[0.9, 0.9, -1.0, 0.1, 0.1]], dtype=np.float32)
    written = np.array([[True, True, False, True, True]])
    fill_holes(color, depth, written, source, "simple")
    assert color[0, 2, 2] == 255


def test_high_fill_respects_color():
    """高品質版は、色が離れた遠い隣より、同じ色の隣を使う。"""
    color = np.zeros((1, 5, 3), dtype=np.uint8)
    source = np.zeros((1, 5, 3), dtype=np.uint8)
    color[0, 1] = (255, 0, 0)
    color[0, 3] = (0, 0, 255)
    source[0, 2] = (255, 0, 0)
    depth = np.array([[0.9, 0.9, -1.0, 0.1, 0.1]], dtype=np.float32)
    written = np.array([[True, True, False, True, True]])
    fill_holes(color, depth, written, source, "high")
    assert color[0, 2, 0] == 255
    assert color[0, 2, 2] == 0
