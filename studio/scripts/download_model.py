# SPDX-License-Identifier: Apache-2.0
"""Depth Anything V2 Small の ONNX を studio/models へ置く。"""

from __future__ import annotations

import urllib.request
from pathlib import Path

# TODO(要確認): 公式カードのファイル配置が変わったら、この URL を更新する。
MODEL_URL = (
    "https://huggingface.co/onnx-community/"
    "depth-anything-v2-small-ONNX/resolve/main/onnx/model.onnx"
)


def main() -> None:
    """モデルが無いときだけダウンロードする。"""
    destination = Path(__file__).resolve().parents[1] / "models"
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / "depth_anything_v2_small.onnx"
    if target.is_file():
        print(target)
        return
    # 取得先を固定し、Base 以上の重みは取らない。
    request = urllib.request.Request(
        MODEL_URL,
        headers={"User-Agent": "PrismShotFrame"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        target.write_bytes(response.read())
    print(target)


if __name__ == "__main__":
    main()
