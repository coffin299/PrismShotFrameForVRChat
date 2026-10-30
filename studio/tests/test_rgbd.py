# SPDX-License-Identifier: Apache-2.0
"""RGB-D の目印と往復。"""

import numpy as np

from prismshot.io.rgbd import decode_depth, encode_depth, is_rgbd, pack_rgbd, split_rgbd


def test_depth_roundtrip():
    """16bit に往復しても、近いほど白いまま戻る。"""
    depth = np.linspace(0.0, 1.0, 16, dtype=np.float32).reshape(4, 4)
    restored = decode_depth(encode_depth(depth))
    assert np.allclose(restored, depth, atol=1.0 / 255.0)


def test_marker_roundtrip():
    """結合した画像から、距離と深度が戻る。"""
    color = np.full((16, 16, 3), 128, dtype=np.uint8)
    depth = np.full((16, 16), 0.5, dtype=np.float32)
    packed = pack_rgbd(color, depth, 0.3, 10.0)
    assert is_rgbd(packed)
    got = split_rgbd(packed)
    assert got.near_m == 0.3
    assert got.far_m == 10.0
    # 深度の左上は目印の外なので、量子化誤差だけを見る。
    assert abs(float(got.depth[0, 0]) - 0.5) < 0.001


def test_block_marker_and_flip():
    """太い区画と、上下が逆の画像も読む。"""
    color = np.full((32, 32, 3), 20, dtype=np.uint8)
    depth = np.full((32, 32), 0.25, dtype=np.float32)
    packed = pack_rgbd(color, depth, 1.5, 8.0, step=4)
    assert is_rgbd(packed)
    flipped = np.flipud(packed)
    got = split_rgbd(flipped)
    assert got.near_m == 1.5
    assert got.far_m == 8.0


def test_plain_photo_is_not_rgbd():
    """目印の無い写真は RGB-D にしない。"""
    plain = np.full((12, 12, 3), 10, dtype=np.uint8)
    assert not is_rgbd(plain)
