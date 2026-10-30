# SPDX-License-Identifier: Apache-2.0
"""OSCQuery の解釈と、モデルが無いときのエラー。"""

from pathlib import Path

import numpy as np

from prismshot.depth.estimator import DepthModelError, estimate_depth
from prismshot.osc.client import parse_oscquery_port, tree_has_shot


def test_parse_oscquery_port():
    """ログの最後のポートを採用する。"""
    text = "Advertising Service VRChat-Client-A of type OSCQuery on 42069\nOSCQuery on 45000\n"
    assert parse_oscquery_port(text) == 45000
    assert parse_oscquery_port("no port") is None


def test_tree_has_shot_nested_and_flat():
    """ネストとフラットの両方で Shot を見つける。"""
    nested = {
        "CONTENTS": {
            "avatar": {
                "CONTENTS": {
                    "parameters": {
                        "CONTENTS": {
                            "PrismShot": {"CONTENTS": {"Enable": {"TYPE": "T"}}}
                        }
                    }
                }
            }
        }
    }
    flat = {"CONTENTS": {"avatar": {"CONTENTS": {"parameters": {"CONTENTS": {"PrismShot/Enable": {}}}}}}}
    assert tree_has_shot(nested)
    assert tree_has_shot(flat)
    assert not tree_has_shot({"CONTENTS": {"avatar": {}}})


def test_missing_model_raises():
    """重みが無いときは、実行環境が無くても理由を返す。"""
    color = np.zeros((4, 4, 3), dtype=np.uint8)
    try:
        estimate_depth(color, model_path=Path("missing-depth-model.onnx"))
    except DepthModelError as exc:
        assert "深度モデルがありません" in str(exc)
    else:
        raise AssertionError("モデル欠如を見逃しました")
