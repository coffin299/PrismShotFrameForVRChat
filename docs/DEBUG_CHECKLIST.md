# デバッグチェックリスト

Unity、VRChat、GPU では未実行です。ここは手元で上から確認するための手順です。

## 1. 環境

Studio。venv は作らない。

```powershell
cd studio
py -3.11 -m pip install -e ".[dev]"
$env:PYTHONDONTWRITEBYTECODE = "1"
py -3.11 -m pytest
py -3.11 scripts/download_model.py
py -3.11 -m prismshot
```

`onnxruntime` は入れない。

Unity は 2022.3.22f1。アバタープロジェクトに Shot の `Packages/com.prismshotframe.shot`、ワールドプロジェクトに Frame の `Packages/com.prismshotframe.frame` を追加する。

メニュー:

- `PrismShot/Build Shot Prefab` → `Assets/PrismShotFrame/Generated/PrismShot.prefab`
- `PrismShot/Build Frame Prefabs`
- `PrismShot/Read Picture Name On Selection`
- `PrismShot/Create Sample Scene` → `Assets/PrismShotFrame/Generated/Sample.unity`（今のシーンは置き換わる）

## 2. 確認手順

### Studio

1. 普通の写真を開く。モデルがあれば深度が付く。無ければステータスに理由が出て、アプリは落ちない。
   - 関係: `studio/prismshot/depth/estimator.py`、`studio/prismshot/ui/main_window.py`
2. プレビュー上でマウスを左右に動かし、視点が変わる。深度を並べて表示できる。
3. キルト、左右並び、RGB-D を書き出す。長辺が 1920 を超える元画像も縮小されない。透かしは無い。
   - キルト名は `元の名前_qs{列}x{行}a{縦横比}.png`。視点0は左下、最後は右上。
4. 複数選択で一括書き出しし、枚数ぶんのファイルができる。
5. 輪郭補正と高品質な穴埋めを切り替えて、書き出しが落ちない。

期待: `pytest` が失敗しない。

### Shot

1. プレハブをアバターに付けてアップロードする。メニューに「出す」「近い距離」「遠い距離」「ズーム」「深度プレビュー」がある。
2. 出すまで、カメラが負荷を増やさない。
3. カードを画面いっぱいに撮る。左が色、右が深度。Studio がその PNG を RGB-D として開く。
4. Android 向けビルドでは Shot が消える。

ログ: VRChat の `output_log`。関係: `Editor/PrismShotPrefabBuilder.cs`、`Editor/PrismShotQuestStrip.cs`、`Runtime/Shaders/PrismShotDepthEncode.shader`、`Runtime/Shaders/PrismShotComposite.shader`。

### OSC

1. VRChat の OSC を有効にして Studio を開く。未起動なら「見つかりません」と出て落ちない。
2. Shot 入りのアバターで、スライダーが距離とズームを変える。
3. シャッターのあと、数秒以内に新しい RGB-D がプレビューへ出る。

関係: `studio/prismshot/osc/client.py`、`studio/prismshot/osc/watcher.py`、`docs/osc_parameters.md`。

### Frame

1. サンプルシーンで、キルトは横へ移動すると視点が混ざる。RGB-D は横へ移動すると絵がずれる。
2. Quest では RGB-D の額縁を使い、枚数を増やしても極端に重くならないかを見る。
3. スライドショーが画像を差し替える。

関係: `Runtime/Shaders/PrismShotFrameQuilt.shader`、`Runtime/Shaders/PrismShotFrameRGBD.shader`、`Runtime/Udon/PrismShotSlideshow.cs`。

## 3. TODO(要確認)

| ファイル | 行 | 内容 |
| --- | --- | --- |
| studio/scripts/download_model.py | 9 | ONNX の URL |
| studio/prismshot/depth/estimator.py | 52 | 出力の遠近が逆の ONNX |
| unity/.../PrismShotDepthEncode.shader | 2 | アバターカメラ自身の深度か |
| unity/.../PrismShotComposite.shader | 2 | 色変換で目印が壊れるか |
| unity/.../PrismShotQuestStrip.cs | 10 | ビルド前処理が今の SDK で呼ばれるか |
| unity/.../PrismShotPrefabBuilder.cs | 15 | レイヤー4をメインカメラが見るか |
| unity/.../PrismShotFrameQuilt.shader | 2 | シングルパスステレオで視点が分かれるか |
| unity/.../PrismShotFrameRGBD.shader | 2 | Linear 色空間で深度バイトが戻るか |

## 4. 既知の未検証と疑い

- pytest、Unity、VRChat、DirectML は、この環境では実行していない。
- アバターカメラの `_CameraDepthTexture` が古い深度だと、Shot の右半分は使えない。その場合は Studio の AI 深度を使う。
- カードが写真の隅に無いと、RGB-D と判定されない。カードを画面いっぱいに撮る。
- 写真が JPEG だと、16bit の深度と目印が劣化する。PNG 想定。
- Write Defaults を切っている。アバター側の設定とぶつかると、しまう操作後にカメラが残ることがある。
- asmdef の `VRC.SDK3A`、`VRC.SDKBase.Editor`、`nadena.dev.modular-avatar.core`、`UdonSharp.Runtime` は、導入した版の名前と違うとコンパイルできない。
- 輪郭補正は色の勾配だけを見ている。髪の毛専用のモデルは入っていない。
- スライドショーは同期しない。人によってコマがずれる。

## 5. 人間がまだ見ること

- 「PrismShotFrame」の商標（J-PlatPat の第9類、第41類、第42類）。
- Depth Anything V2 Small の学習データが、公式の Apache-2.0 表記と矛盾しないか。
