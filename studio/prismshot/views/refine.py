# SPDX-License-Identifier: Apache-2.0
"""色の境界を残して、平坦な部分の深度をなだらかにする。"""

from __future__ import annotations

import cv2
import numpy as np


def refine_depth(color: np.ndarray, depth: np.ndarray) -> np.ndarray:
    """追加の学習モデルは使わず、色の勾配が弱い場所だけ深度をぼかす。"""
    if color.shape[:2] != depth.shape[:2]:
        raise ValueError("色と深度の大きさが違います")
    gray = cv2.cvtColor(color[:, :, :3], cv2.COLOR_RGB2GRAY)
    # 色の境界の強さを 0〜1 にする。
    gradient_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gradient_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = np.sqrt(gradient_x * gradient_x + gradient_y * gradient_y)
    edge = np.clip(magnitude / 64.0, 0.0, 1.0).astype(np.float32)
    smooth = cv2.GaussianBlur(depth.astype(np.float32), (0, 0), 2.0)
    # 境界は元の深度を残し、平坦な場所だけ平滑化する。
    mixed = smooth * (1.0 - edge) + depth.astype(np.float32) * edge
    return np.clip(mixed, 0.0, 1.0).astype(np.float32)
