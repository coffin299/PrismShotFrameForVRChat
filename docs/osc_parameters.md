# OSC パラメータ

すべてローカル専用です。ネットワークのビットは使いません。アドレスは `/avatar/parameters/` の後ろに名前を付けます。

| 名前 | 型 | 範囲 | 意味 |
| --- | --- | --- | --- |
| PrismShot/Enable | Bool | 0 / 1 | カメラを出す |
| PrismShot/NearDistance | Float | 0〜1 | 近い距離。0 が 0.15m、1 が 5m |
| PrismShot/FarDistance | Float | 0〜1 | 遠い距離。0 が 1m、1 が 30m |
| PrismShot/Zoom | Float | 0〜1 | 視野角。0 が 20 度、1 が 70 度 |
| PrismShot/DepthPreview | Bool | 0 / 1 | 深度の見本を出す |

標準カメラのシャッターはアバターパラメータではありません。

| アドレス | 型 | 意味 |
| --- | --- | --- |
| /usercamera/Mode | Int | 1 で写真モード |
| /usercamera/Capture | Bool | 撮影 |

送信先は UDP `127.0.0.1:9000`。OSCQuery のポートは VRChat のログから読みます。
