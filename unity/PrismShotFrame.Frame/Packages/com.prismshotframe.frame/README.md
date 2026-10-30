# PrismShotFrame Frame

ワールドに置く額縁です。初期マテリアルは RGB-D で、Quest でも軽い表示にします。

## 入れ方

1. Unity 2022.3.22f1 のワールド用プロジェクトを開く。
2. VRChat Worlds SDK と UdonSharp を入れる。
3. `Packages/com.prismshotframe.frame` をローカルパッケージとして追加する。
4. メニュー `PrismShot/Build Frame Prefabs` を実行する。
5. できたプレハブをシーンに置く。
6. Picture のマテリアルへ画像を入れ、`PrismShot/Read Picture Name On Selection` を実行する。ファイル名が `qs8x6a0.75` の形ならキルト用シェーダーに切り替わる。

`PrismShot/Create Sample Scene` は、3種類の額縁を置いたシーンを作ります。今開いているシーンは置き換わるので、先に保存してください。

スライドショーは各人の端末で進みます。画像の種類と列・行は、並べる全部で揃えてください。

asmdef の `UdonSharp.Runtime` が見つからない場合は、プロジェクト内の UdonSharp のアセンブリ名に合わせてください。
