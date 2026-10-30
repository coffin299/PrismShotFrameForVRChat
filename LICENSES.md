# ライセンス

このリポジトリのコードは Apache-2.0。著作権は coffin299。

商用に使えない依存は入れていない。版は実装時点の下限で、インストール時に新しい版が入ることがある。

| 名前 | 版の下限 | ライセンス | 商用 | 用途 |
| --- | --- | --- | --- | --- |
| PySide6 | 6.6 | LGPL-3.0 | 可（改変せず動的リンク） | Studio の画面 |
| onnxruntime-directml | 1.17 | MIT | 可 | 深度推定。CPU 実行も含む |
| NumPy | 1.26 | BSD-3-Clause | 可 | 配列 |
| opencv-python | 4.9 | Apache-2.0 | 可 | 画像処理 |
| Pillow | 10.0 | HPND | 可 | 画像の読み書き |
| python-osc | 1.8 | BSD-3-Clause | 可 | OSC 送信 |
| watchdog | 4.0 | Apache-2.0 | 可 | 写真フォルダの監視 |
| pytest | 8.0 | MIT | 可 | 開発時のテストのみ |
| Depth Anything V2 Small | 公式の Small 重み | Apache-2.0（公式表記） | 公式表記では可 | 深度推定。学習データの確認は未了 |
| Modular Avatar | 1.9.0 | MIT | 可 | Shot の導入。同梱しない |
| UdonSharp | 1.1.9 | MIT | 可 | Frame のスライドショー。同梱しない |
| VRChat SDK | 3.7 以降 | VRChat の利用条件 | SDK の条件に従う | 同梱しない |

PySide6 は改変しない。PyInstaller で配るときは1フォルダ形式にし、Qt の差し替えができる状態を崩さない。

`onnxruntime` と `onnxruntime-directml` は同時に入れない。DirectML 版だけで CPU にも落ちる。

Depth Anything V2 の Base / Large / Giant は CC-BY-NC-4.0 なので使わない。

Looking Glass の SDK、ソフト、シェーダーは同梱しない。
