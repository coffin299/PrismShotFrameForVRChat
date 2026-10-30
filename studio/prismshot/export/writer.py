# SPDX-License-Identifier: Apache-2.0
"""書き出し。解像度の上限も透かしも付けない。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from prismshot.views.quilt import build_quilt, quilt_filename
from prismshot.views.shift import synthesize_views
from prismshot.io.rgbd import pack_rgbd


def save_png(image: np.ndarray, path: Path) -> Path:
    """RGB の PNG を、縮小せずに書く。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.ascontiguousarray(image[:, :, :3]), mode="RGB").save(path)
    return path


def export_rgbd(
    color: np.ndarray,
    depth: np.ndarray,
    near_m: float,
    far_m: float,
    path: Path,
) -> Path:
    """色と深度を横並びにした PNG を書く。"""
    return save_png(pack_rgbd(color, depth, near_m, far_m), path)


def export_sbs(
    color: np.ndarray,
    depth: np.ndarray,
    disparity: float,
    focus: float,
    quality: str,
    path: Path,
) -> Path:
    """左が左端視点、右が右端視点の画像を書く。"""
    views = synthesize_views(color, depth, 2, disparity, focus, quality)
    side_by_side = np.concatenate(views, axis=1)
    return save_png(side_by_side, path)


def export_quilt(
    color: np.ndarray,
    depth: np.ndarray,
    views: list[np.ndarray],
    columns: int,
    rows: int,
    stem: str,
    directory: Path,
) -> Path:
    """キルトを、規則どおりのファイル名で書く。"""
    aspect = color.shape[1] / float(color.shape[0])
    name = quilt_filename(stem, columns, rows, aspect)
    return save_png(build_quilt(views, columns, rows), directory / name)
