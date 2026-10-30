# PrismShotFrame マニュアル

完全無料です。ライセンスキー、透かし、解像度の上限はありません。

Looking Glass Portrait / Go で表示できます（※Looking Glassは Looking Glass Factory の商標です）。

## 用意するもの

- Windows
- Python 3.11（Studio）
- Unity 2022.3.22f1（Shot と Frame）
- VRChat Creator Companion
- アバター用に Modular Avatar 1.9 以降
- ワールド用に UdonSharp

## Studio

venv は作りません。`studio` フォルダで次を実行します。

```powershell
py -3.11 -m pip install -e ".[dev]"
$env:PYTHONDONTWRITEBYTECODE = "1"
py -3.11 -m pytest
py -3.11 scripts/download_model.py
py -3.11 -m prismshot
```

`onnxruntime` は入れないでください。`onnxruntime-directml` だけで GPU と CPU の両方に対応します。

画面では、VRChat の写真フォルダを一覧できます。ドラッグ＆ドロップでも開けます。RGB-D の目印が無い写真は、Depth Anything V2 Small で深度を推定します。モデルが無いときは、その旨を表示して終了しません。

調整できるのは、視差、ピント、列、行、穴埋め（単純 / 高品質）、輪郭補正です。プレビューの上でマウスを左右に動かすと視点が変わります。書き出しはキルト、左右並び、RGB-D です。一覧で複数選ぶと一括変換できます。

キルトの名前は `元の名前_qs{列}x{行}a{縦横比}.png` です。縦長の初期値は 8x6、横長は 11x6 です。

## Shot

1. アバター用プロジェクト（Unity 2022.3.22f1）に、VRChat Avatars SDK と Modular Avatar を入れる。
2. `unity/PrismShotFrame.Shot/Packages/com.prismshotframe.shot` をローカルパッケージとして追加する。
3. メニュー `PrismShot/Build Shot Prefab` を実行する。
4. `Assets/PrismShotFrame/Generated/PrismShot.prefab` を手の下に置く。
5. アップロードする。

メニューの「出す」までカメラは描画しません。Quest 向けのビルドでは、この部品を削除します。

撮影するときは、背面のカードが VRChat の写真いっぱいに写るようにします。カードの左が色、右が深度です。深度の見本は別の小さな板で、写真には入りません。

## OSC

VRChat の OSC を有効にします。Studio の「再接続」で、ログから OSCQuery を探します。Shot の入ったアバターなら、出し入れ、距離、ズーム、深度プレビュー、シャッターを送れます。VRChat が起動していなくても Studio は落ちません。

パラメータの一覧は [osc_parameters.md](osc_parameters.md) です。

写真フォルダに RGB-D が増えると、Studio がプレビューへ取り込みます。

## Frame

1. ワールド用プロジェクトに Worlds SDK と UdonSharp を入れる。
2. `unity/PrismShotFrame.Frame/Packages/com.prismshotframe.frame` を追加する。
3. `PrismShot/Build Frame Prefabs` を実行する。
4. プレハブを置き、Picture のマテリアルに画像を入れる。
5. Picture を選んで `PrismShot/Read Picture Name On Selection` を実行する。

ファイル名に `qs8x6` のような部分があればキルト用シェーダーになります。無ければ RGB-D のままです。Quest では RGB-D を使ってください。

額縁は平面、縁付き、厚み付きの3種です。スライドショーは Picture の親に付いています。並べる画像は種類と列・行を揃えます。各人の端末で時間が進みます。

`PrismShot/Create Sample Scene` は、今のシーンを新しいシーンに置き換えます。先に保存してください。

## うまくいかないとき

- 普通の写真として扱われる: カードが写真いっぱいに写っていない。AI 深度を使うか、カードを画面いっぱいにして撮り直す。
- 深度がおかしい: Studio で「AI 深度を使う」をオンにする。アバターカメラの深度は未確認です。
- カードが見えない: レイヤー 4 をメインカメラが見ていない可能性がある。
- コンパイルエラー: パッケージの asmdef にある参照名を、プロジェクトのアセンブリ名に合わせる。

詳細な確認手順は [DEBUG_CHECKLIST.md](DEBUG_CHECKLIST.md) です。
