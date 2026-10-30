# SPDX-License-Identifier: Apache-2.0
"""読み込みから書き出しまでの共通手順。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from prismshot.depth.estimator import estimate_depth
from prismshot.export.writer import export_quilt, export_rgbd, export_sbs
from prismshot.io.rgbd import is_rgbd, split_rgbd
from prismshot.views.quilt import preset_grid
from prismshot.views.refine import refine_depth
from prismshot.views.shift import synthesize_views


@dataclass
class ExportSettings:
    """画面と一括変換が共有する設定。"""

    disparity: float = 24.0
    focus: float = 0.5
    columns: int = 0
    rows: int = 0
    hole_quality: str = "simple"
    edge_refine: bool = False
    force_ai: bool = False


@dataclass
class LoadedPhoto:
    """1枚の色、深度、距離、AI を使ったか。"""

    color: np.ndarray
    depth: np.ndarray
    near_m: float
    far_m: float
    used_ai: bool


def load_rgb(path: Path) -> np.ndarray:
    """画像を RGB の uint8 配列で開く。"""
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def load_photo(
    path: Path,
    force_ai: bool = False,
    model_path: Path | None = None,
) -> LoadedPhoto:
    """RGB-D なら分解し、そうでなければ深度を推定する。"""
    image = load_rgb(path)
    if not force_ai and is_rgbd(image):
        packed = split_rgbd(image)
        return LoadedPhoto(packed.color, packed.depth, packed.near_m, packed.far_m, False)
    depth = estimate_depth(image, model_path)
    return LoadedPhoto(image, depth, 0.3, 10.0, True)


def resolve_grid(width: int, height: int, settings: ExportSettings) -> tuple[int, int]:
    """列と行が指定されていればそれを使い、無ければ縦横から決める。"""
    if settings.columns > 0 and settings.rows > 0:
        return settings.columns, settings.rows
    return preset_grid(width, height)


def prepare_depth(color: np.ndarray, depth: np.ndarray, settings: ExportSettings) -> np.ndarray:
    """輪郭補正がオンのときだけ深度をならす。"""
    if settings.edge_refine:
        return refine_depth(color, depth)
    return depth.astype(np.float32)


def make_views(
    color: np.ndarray,
    depth: np.ndarray,
    settings: ExportSettings,
) -> tuple[list[np.ndarray], int, int]:
    """キルト用の全視点を作る。"""
    columns, rows = resolve_grid(color.shape[1], color.shape[0], settings)
    working = prepare_depth(color, depth, settings)
    views = synthesize_views(
        color,
        working,
        columns * rows,
        settings.disparity,
        settings.focus,
        settings.hole_quality,
    )
    return views, columns, rows


def export_one(
    path: Path,
    settings: ExportSettings,
    out_dir: Path,
    kind: str,
    model_path: Path | None = None,
) -> Path:
    """1枚を指定の形式で書き出す。"""
    loaded = load_photo(path, settings.force_ai, model_path)
    depth = prepare_depth(loaded.color, loaded.depth, settings)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = path.stem
    if kind == "rgbd":
        return export_rgbd(loaded.color, depth, loaded.near_m, loaded.far_m, out_dir / f"{stem}_rgbd.png")
    if kind == "sbs":
        return export_sbs(
            loaded.color,
            depth,
            settings.disparity,
            settings.focus,
            settings.hole_quality,
            out_dir / f"{stem}_sbs.png",
        )
    if kind == "quilt":
        views, columns, rows = make_views(loaded.color, loaded.depth, settings)
        return export_quilt(loaded.color, depth, views, columns, rows, stem, out_dir)
    raise ValueError(f"未知の形式です: {kind}")


def export_batch(
    paths: list[Path],
    settings: ExportSettings,
    out_dir: Path,
    kind: str,
    model_path: Path | None = None,
) -> list[Path]:
    """複数枚を、枚数ぶんのファイルにする。"""
    return [export_one(path, settings, out_dir, kind, model_path) for path in paths]
