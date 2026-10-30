# SPDX-License-Identifier: Apache-2.0
"""書き出しに透かしも縮小も無いことと、一括変換。"""

from pathlib import Path

import numpy as np
from PIL import Image

from prismshot.export.writer import export_rgbd
from prismshot.io.rgbd import pack_rgbd
from prismshot.pipeline import ExportSettings, export_batch


def test_no_cap_and_no_watermark(tmp_path: Path):
    """長辺が 1920 を超えても縮小せず、指定した色が残る。"""
    color = np.full((8, 2000, 3), 10, dtype=np.uint8)
    depth = np.ones((8, 2000), dtype=np.float32)
    path = export_rgbd(color, depth, 0.3, 10.0, tmp_path / "big.png")
    saved = np.asarray(Image.open(path))
    assert saved.shape[1] == 4000
    # 目印は隅だけなので、色側の内側は元の値のまま。
    assert int(saved[4, 40, 0]) == 10


def test_batch_writes_one_file_per_input(tmp_path: Path):
    """RGB-D を枚数ぶん書き出す。"""
    folder = tmp_path / "in"
    folder.mkdir()
    color = np.full((8, 8, 3), 30, dtype=np.uint8)
    depth = np.full((8, 8), 0.4, dtype=np.float32)
    paths = []
    for index in range(2):
        packed = pack_rgbd(color, depth, 0.3, 10.0)
        path = folder / f"shot{index}.png"
        Image.fromarray(packed, mode="RGB").save(path)
        paths.append(path)
    written = export_batch(paths, ExportSettings(), tmp_path / "out", "rgbd")
    assert len(written) == 2
    assert all(path.is_file() for path in written)
