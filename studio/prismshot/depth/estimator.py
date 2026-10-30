# SPDX-License-Identifier: Apache-2.0
"""Depth Anything V2 Small による相対深度。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import cv2
import numpy as np

# ImageNet の正規化。このモデルの前処理として公式例と同じ値を使う。
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class DepthModelError(RuntimeError):
    """モデルが無い、または推論できない。"""


def default_model_path() -> Path:
    """環境変数、実行ファイル横、リポジトリの models の順で場所を決める。"""
    env = os.environ.get("PRISMSHOT_MODEL")
    if env:
        return Path(env)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "models" / "depth_anything_v2_small.onnx"
    # depth/estimator.py から見て studio/models。
    return Path(__file__).resolve().parents[2] / "models" / "depth_anything_v2_small.onnx"


def estimate_depth(color: np.ndarray, model_path: Path | None = None) -> np.ndarray:
    """RGB 画像から、近いほど 1 の深度を返す。"""
    path = Path(model_path) if model_path is not None else default_model_path()
    if not path.is_file():
        raise DepthModelError(f"深度モデルがありません: {path}")
    # インポートはファイルがあるときだけ行い、テストが実行環境を要求しない。
    import onnxruntime as ort

    available = ort.get_available_providers()
    providers: list[str] = []
    if "DmlExecutionProvider" in available:
        providers.append("DmlExecutionProvider")
    providers.append("CPUExecutionProvider")
    session = ort.InferenceSession(str(path), providers=providers)
    input_meta = session.get_inputs()[0]
    height, width = _input_size(input_meta.shape)
    blob = _prepare(color[:, :, :3], width, height)
    raw = session.run(None, {input_meta.name: blob})[0]
    depth = _normalize_closer_is_one(np.squeeze(raw))
    # TODO(要確認): 別の ONNX で遠近が逆なら、ここで反転する。
    resized = cv2.resize(depth, (color.shape[1], color.shape[0]), interpolation=cv2.INTER_LINEAR)
    return np.clip(resized, 0.0, 1.0).astype(np.float32)


def _input_size(shape: list[object]) -> tuple[int, int]:
    """静的な高さと幅があればそれを使い、無ければ 518 にする。"""
    if len(shape) >= 4 and isinstance(shape[2], int) and isinstance(shape[3], int):
        return int(shape[2]), int(shape[3])
    return 518, 518


def _prepare(color: np.ndarray, width: int, height: int) -> np.ndarray:
    """NCHW の float32 バッチを作る。"""
    resized = cv2.resize(color, (width, height), interpolation=cv2.INTER_LINEAR)
    array = resized.astype(np.float32) / 255.0
    array = (array - MEAN) / STD
    return np.transpose(array, (2, 0, 1))[None, ...]


def _normalize_closer_is_one(raw: np.ndarray) -> np.ndarray:
    """相対値の最大を近い側の 1 にする。"""
    plane = raw.astype(np.float32)
    shifted = plane - float(plane.min())
    scale = float(shifted.max())
    if scale < 1e-6:
        return np.zeros_like(plane, dtype=np.float32)
    return shifted / scale
