# SPDX-License-Identifier: Apache-2.0
"""輪郭補正が範囲を守ること。"""

import numpy as np

from prismshot.views.refine import refine_depth


def test_refine_stays_in_range():
    """出力の大きさと 0〜1 の範囲を崩さない。"""
    color = np.zeros((12, 16, 3), dtype=np.uint8)
    color[:, :8] = (255, 0, 0)
    color[:, 8:] = (0, 0, 255)
    depth = np.random.default_rng(0).random((12, 16)).astype(np.float32)
    refined = refine_depth(color, depth)
    assert refined.shape == depth.shape
    assert float(refined.min()) >= 0.0
    assert float(refined.max()) <= 1.0
