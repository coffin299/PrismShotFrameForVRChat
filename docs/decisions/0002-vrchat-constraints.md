# 0002 VRChat の制約

確認日の時点で、公式ドキュメントと公開されている不具合報告から次のように扱う。

## 確認できたこと

- SDK 用の Unity は 2022.3.22f1。クライアントが Unity 6 でも、SDK プロジェクトは上げない。
- Quest / Android のアバターでは Camera が無効で、カスタムシェーダーも使えない。
- ワールドではカスタムシェーダーが使える。透過の塗りつぶしは Quest で重い。
- アバターに任意の MonoBehaviour は残せない。Shot は Camera、RenderTexture、Animator、マテリアルだけで動かす。
- OSC の初期値は、送信 UDP 9000、受信 UDP 9001。OSCQuery の TCP ポートはログの `OSCQuery on <port>` で分かる。
- 標準カメラの撮影は `/usercamera/Capture`。写真モードは `/usercamera/Mode` の 1。
- Modular Avatar の Platform Filter は VRChat と Resonite の区別であり、Quest ビルドから部品を消す用途には使わない。

## 仮の実装

- 深度は、深度カメラの `depthTextureMode = Depth` と透過板のシェーダーで色にする。アバターカメラの深度がメインカメラの古いバッファになる報告があるため、`TODO(要確認)` を付けた。崩れた場合は Studio で AI 深度に切り替える。
- Quest 向けアバターでは、アップロード前の `IVRCSDKPreprocessAvatarCallback` で Shot ルートを削除する。
- カードと本体は Unity のレイヤー 4、深度用の板はレイヤー 2 に置く。メインカメラから見えるかは要確認。
- 写真は PNG 想定。ファイル名は VRChat が付けるので、判別は画像内の目印だけ。

## パラメータ

Shot のパラメータはメニューと OSC から触るが、ネットワーク同期はしない。Modular Avatar では `syncType` を Bool または Float にし、`localOnly` を有効にする。`NotSynced` は Expression Parameters へ登録されないため使わない。
