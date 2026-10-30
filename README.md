# PrismShotFrame

VRChat で撮った写真を、見る角度で奥行きが変わる立体写真にして、ワールドの額縁に飾るための無料の道具です。

部品は3つです。

| 部品 | 役割 | 動く場所 |
| --- | --- | --- |
| Shot | 色と深度を1回で撮る | アバター（PC） |
| Studio | 多視点画像、左右並び、RGB-D を作る。OSC で Shot を操作する | Windows |
| Frame | キルトか RGB-D を立体に見せる | ワールド（PC と Quest） |

Looking Glass Portrait / Go で表示できます（※Looking Glassは Looking Glass Factory の商標です）。

ライセンスキー、透かし、解像度の上限はありません。

## リポジトリ

- [Studio](studio/)
- [Shot](unity/PrismShotFrame.Shot/Packages/com.prismshotframe.shot/)
- [Frame](unity/PrismShotFrame.Frame/Packages/com.prismshotframe.frame/)
- [マニュアル（日本語）](docs/manual_ja.md)
- [Manual (English)](docs/manual_en.md)
- [概要ページ](docs/index.html)
- [デバッグ手順](docs/DEBUG_CHECKLIST.md)

## Studio を動かす

venv は作らない。依存の導入、モデルの取得、テストは次を、使う Python 3.11 で実行する。

```powershell
cd studio
py -3.11 -m pip install -e ".[dev]"
$env:PYTHONDONTWRITEBYTECODE = "1"
py -3.11 -m pytest
py -3.11 scripts/download_model.py
py -3.11 -m prismshot
```

`onnxruntime` は入れない。`onnxruntime-directml` だけを使う。

## Unity

エディタは 2022.3.22f1。アバター用プロジェクトに Shot のパッケージを、ワールド用プロジェクトに Frame のパッケージを追加する。手順はマニュアルにある。

## ライセンス

Apache-2.0。第三者コンポーネントは [LICENSES.md](LICENSES.md)。
