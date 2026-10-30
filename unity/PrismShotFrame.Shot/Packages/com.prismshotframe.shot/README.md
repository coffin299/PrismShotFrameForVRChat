# PrismShotFrame Shot

PC のアバターに付けるカメラです。Quest 向けビルドでは、アップロード前にこの部品を削除します。

## 入れ方

1. Unity 2022.3.22f1 のアバター用プロジェクトを開く。
2. VCC で VRChat Avatars SDK と Modular Avatar 1.9 以降を入れる。
3. このフォルダの `Packages/com.prismshotframe.shot` をローカルパッケージとして追加する。
4. メニュー `PrismShot/Build Shot Prefab` を実行する。
5. できた `Assets/PrismShotFrame/Generated/PrismShot.prefab` を、アバターの手の下に置く。

カメラはメニューの「出す」まで描画しません。パラメータはネットワーク同期しません。

asmdef の参照名がプロジェクトと違うときは、Editor の asmdef を合わせてください。
