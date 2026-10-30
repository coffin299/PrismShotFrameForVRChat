# 0001 深度推定モデル

## 決定

普通の写真の深度は **Depth Anything V2 Small** だけを使う。

- 公式 README は Small の重みを Apache-2.0 としている。
- Base / Large / Giant は CC-BY-NC-4.0 なので、配布物にも開発環境にも入れない。
- 実行形式は ONNX。取得先の候補は `onnx-community/depth-anything-v2-small-ONNX`（Apache-2.0）。
- ファイル名は `studio/models/depth_anything_v2_small.onnx`。Git では管理しない。
- 入力は 518x518、ImageNet の平均と分散で正規化する。
- この ONNX は値が大きいほど近い、という相対深度を出す前提で、0〜1 に正規化して近い方を 1 にする。

## 未確認

学習データのライセンスが重みの Apache-2.0 と矛盾しないかは、公式 issue で未回答の指摘がある。配布前に人間が確認する。
