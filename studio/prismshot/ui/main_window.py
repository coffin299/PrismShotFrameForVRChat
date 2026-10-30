# SPDX-License-Identifier: Apache-2.0
"""写真の取り込み、プレビュー、書き出し、カメラ操作。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, QTimer, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from prismshot.io.gallery import is_image_path, list_photos, vrchat_picture_dir
from prismshot.osc.client import OscController
from prismshot.osc.watcher import PhotoWatcher
from prismshot.pipeline import ExportSettings, LoadedPhoto, export_batch, load_photo, make_views


def _rgb_to_qimage(array: np.ndarray) -> QImage:
    """配列の寿命が終わっても残る RGB 画像にする。"""
    frame = np.ascontiguousarray(array[:, :, :3])
    height, width, _ = frame.shape
    image = QImage(frame.data, width, height, width * 3, QImage.Format.Format_RGB888)
    return image.copy()


def _depth_view(depth: np.ndarray) -> np.ndarray:
    """近いほど白い深度の見本。"""
    gray = np.rint(np.clip(depth, 0.0, 1.0) * 255.0).astype(np.uint8)
    return np.repeat(gray[:, :, None], 3, axis=2)


class _Job(QThread):
    """重い処理を画面の外で行う。"""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, work) -> None:
        super().__init__()
        self._work = work

    def run(self) -> None:
        try:
            self.succeeded.emit(self._work())
        except Exception as exc:
            self.failed.emit(str(exc))


class PreviewLabel(QLabel):
    """横位置を 0〜1 で知らせるプレビュー。"""

    moved = Signal(float)

    def __init__(self) -> None:
        super().__init__("写真を開いてください")
        self.setMouseTracking(True)
        self.setMinimumSize(480, 320)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mouseMoveEvent(self, event) -> None:
        width = max(self.width(), 1)
        self.moved.emit(min(max(event.position().x() / width, 0.0), 0.999))


class MainWindow(QMainWindow):
    """Studio の主画面。"""

    arrived = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PrismShotFrame Studio")
        self.setAcceptDrops(True)
        self.resize(1100, 720)
        self._loaded: LoadedPhoto | None = None
        self._views: list[np.ndarray] = []
        self._path: Path | None = None
        self._job: _Job | None = None
        self._osc = OscController()
        self._retries = 0
        self._watcher = PhotoWatcher(vrchat_picture_dir(), self._on_file)
        self.arrived.connect(self._import_path)
        self._build()
        self._refresh_gallery()
        self._timer = QTimer(self)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self._poll_osc)
        self._timer.start()
        self._poll_osc()
        self._watcher.start()

    def _build(self) -> None:
        """一覧、プレビュー、操作を横に並べる。"""
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        self.gallery = QListWidget()
        self.gallery.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.gallery.itemSelectionChanged.connect(self._on_select)
        layout.addWidget(self.gallery, 2)
        center = QVBoxLayout()
        self.preview = PreviewLabel()
        self.preview.moved.connect(self._on_preview_x)
        center.addWidget(self.preview, 1)
        self.show_depth = QCheckBox("深度を並べて表示")
        self.show_depth.stateChanged.connect(lambda _value: self._show_current())
        center.addWidget(self.show_depth)
        layout.addLayout(center, 5)
        layout.addLayout(self._controls(), 3)
        self.statusBar().showMessage("準備できました")

    def _controls(self) -> QVBoxLayout:
        """調整、書き出し、OSC の列。"""
        column = QVBoxLayout()
        self.disparity = self._add_slider(column, 0, 80, 24, "視差")
        self.focus = self._add_slider(column, 0, 100, 50, "ピント")
        self.columns = QSpinBox()
        self.rows = QSpinBox()
        for box in (self.columns, self.rows):
            box.setRange(0, 16)
            box.setValue(0)
            box.setSpecialValueText("自動")
        column.addWidget(QLabel("列（0 は自動）"))
        column.addWidget(self.columns)
        column.addWidget(QLabel("行（0 は自動）"))
        column.addWidget(self.rows)
        self.quality = QComboBox()
        self.quality.addItem("単純な穴埋め", "simple")
        self.quality.addItem("高品質な穴埋め", "high")
        column.addWidget(self.quality)
        self.edge = QCheckBox("輪郭補正")
        column.addWidget(self.edge)
        self.force_ai = QCheckBox("AI 深度を使う")
        column.addWidget(self.force_ai)
        self.kind = QComboBox()
        self.kind.addItem("キルト", "quilt")
        self.kind.addItem("左右並び", "sbs")
        self.kind.addItem("RGB-D", "rgbd")
        column.addWidget(self.kind)
        render = QPushButton("立体にする")
        render.clicked.connect(self._render_current)
        column.addWidget(render)
        export = QPushButton("この写真を書き出す")
        export.clicked.connect(self._export_current)
        column.addWidget(export)
        batch = QPushButton("選択を一括書き出し")
        batch.clicked.connect(self._export_batch)
        column.addWidget(batch)
        refresh = QPushButton("写真フォルダを更新")
        refresh.clicked.connect(self._refresh_gallery)
        column.addWidget(refresh)
        column.addWidget(QLabel("カメラ操作"))
        self.osc_label = QLabel("未接続")
        self.osc_label.setWordWrap(True)
        column.addWidget(self.osc_label)
        reconnect = QPushButton("再接続")
        reconnect.clicked.connect(self._poll_osc)
        column.addWidget(reconnect)
        show = QPushButton("カメラを出す")
        show.clicked.connect(lambda: self._send_bool("PrismShot/Enable", True))
        hide = QPushButton("カメラをしまう")
        hide.clicked.connect(lambda: self._send_bool("PrismShot/Enable", False))
        column.addWidget(show)
        column.addWidget(hide)
        self.near = self._add_osc_slider(column, "近い距離", "PrismShot/NearDistance", 3)
        self.far = self._add_osc_slider(column, "遠い距離", "PrismShot/FarDistance", 31)
        self.zoom = self._add_osc_slider(column, "ズーム", "PrismShot/Zoom", 80)
        self.depth_preview = QCheckBox("深度プレビュー")
        self.depth_preview.stateChanged.connect(self._send_depth_preview)
        column.addWidget(self.depth_preview)
        shutter = QPushButton("シャッター")
        shutter.clicked.connect(self._capture)
        column.addWidget(shutter)
        column.addStretch(1)
        self.disparity.sliderReleased.connect(self._render_current)
        self.focus.sliderReleased.connect(self._render_current)
        self.columns.valueChanged.connect(lambda _value: self._render_current())
        self.rows.valueChanged.connect(lambda _value: self._render_current())
        self.quality.currentIndexChanged.connect(lambda _index: self._render_current())
        self.edge.stateChanged.connect(lambda _value: self._render_current())
        self.force_ai.stateChanged.connect(lambda _value: self._open_again())
        return column

    def _add_slider(self, column: QVBoxLayout, low: int, high: int, value: int, title: str) -> QSlider:
        """見出し付きのスライダーを列へ置く。"""
        column.addWidget(QLabel(title))
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(low, high)
        slider.setValue(value)
        column.addWidget(slider)
        return slider

    def _add_osc_slider(self, column: QVBoxLayout, title: str, name: str, value: int) -> QSlider:
        """離したときに、そのパラメータへ 0〜1 を送る。"""
        slider = self._add_slider(column, 0, 100, value, title)
        slider.sliderReleased.connect(lambda source=slider, parameter=name: self._send_float(parameter, source.value() / 100.0))
        return slider

    def _settings(self) -> ExportSettings:
        """画面の値を書き出し設定にする。"""
        return ExportSettings(
            disparity=float(self.disparity.value()),
            focus=self.focus.value() / 100.0,
            columns=self.columns.value(),
            rows=self.rows.value(),
            hole_quality=str(self.quality.currentData()),
            edge_refine=self.edge.isChecked(),
            force_ai=self.force_ai.isChecked(),
        )

    def _refresh_gallery(self) -> None:
        """VRChat の写真を新しい順に最大 100 件出す。"""
        self.gallery.clear()
        for path in list_photos()[:100]:
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.gallery.addItem(item)

    def _on_select(self) -> None:
        """一覧の最後の選択を開く。"""
        items = self.gallery.selectedItems()
        if not items:
            return
        self._open_path(Path(items[-1].data(Qt.ItemDataRole.UserRole)))

    def _open_path(self, path: Path) -> None:
        """読み込んでから視点を作る。"""
        self._path = path
        self._retries = 0
        settings = self._settings()

        def work():
            loaded = load_photo(path, settings.force_ai)
            views, _columns, _rows = make_views(loaded.color, loaded.depth, settings)
            return loaded, views

        self._start_job(work, self._store_render, f"読み込み中: {path.name}")

    def _open_again(self) -> None:
        """AI の切り替えは、ファイルから読み直す。"""
        if self._path is not None:
            self._open_path(self._path)

    def _render_current(self) -> None:
        """開いている写真を、今の設定で作り直す。"""
        if self._loaded is None:
            if self._path is not None:
                self._open_path(self._path)
            return
        loaded = self._loaded
        settings = self._settings()

        def work():
            views, _columns, _rows = make_views(loaded.color, loaded.depth, settings)
            return loaded, views

        self._start_job(work, self._store_render, "視点を作成しています")

    def _store_render(self, result: object) -> None:
        """作った視点をプレビューへ出す。"""
        loaded, views = result
        self._loaded = loaded
        self._views = views
        note = "AI 深度" if loaded.used_ai else "RGB-D"
        self.statusBar().showMessage(f"{note} / 視点 {len(views)} 枚")
        self._show_current()

    def _show_current(self) -> None:
        """先頭の視点、または直前の視点を表示する。"""
        if not self._views or self._loaded is None:
            return
        self._show_index(0)

    def _on_preview_x(self, ratio: float) -> None:
        """マウスの横位置で視点を切り替える。"""
        if not self._views:
            return
        index = int(ratio * len(self._views))
        self._show_index(min(index, len(self._views) - 1))

    def _show_index(self, index: int) -> None:
        """1枚の視点と、必要なら深度を並べる。"""
        if self._loaded is None or not self._views:
            return
        image = self._views[index]
        if self.show_depth.isChecked():
            image = np.concatenate([image, _depth_view(self._loaded.depth)], axis=1)
        pixmap = QPixmap.fromImage(_rgb_to_qimage(image))
        self.preview.setPixmap(
            pixmap.scaled(
                self.preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _export_current(self) -> None:
        """開いている1枚を書き出す。"""
        if self._path is None:
            self.statusBar().showMessage("写真がありません")
            return
        self._export_paths([self._path])

    def _export_batch(self) -> None:
        """一覧で選んだ複数枚を書き出す。"""
        paths = []
        for item in self.gallery.selectedItems():
            paths.append(Path(item.data(Qt.ItemDataRole.UserRole)))
        if not paths and self._path is not None:
            paths = [self._path]
        if not paths:
            self.statusBar().showMessage("写真がありません")
            return
        self._export_paths(paths)

    def _export_paths(self, paths: list[Path]) -> None:
        """保存先を聞いて、選んだ形式で書く。"""
        directory = QFileDialog.getExistingDirectory(self, "書き出し先")
        if not directory:
            return
        settings = self._settings()
        kind = str(self.kind.currentData())

        def work():
            return export_batch(paths, settings, Path(directory), kind)

        self._start_job(work, self._exported, "書き出しています")

    def _exported(self, paths: object) -> None:
        """書き出した枚数を表示する。"""
        self.statusBar().showMessage(f"{len(paths)} 枚を書き出しました")

    def _start_job(self, work, done, message: str) -> None:
        """前の仕事が残っていれば始めない。"""
        if self._job is not None and self._job.isRunning():
            self.statusBar().showMessage("処理中です")
            return
        self.statusBar().showMessage(message)
        job = _Job(work)
        job.succeeded.connect(done)
        job.failed.connect(self._failed)
        job.finished.connect(job.deleteLater)
        self._job = job
        job.start()

    def _failed(self, message: str) -> None:
        """失敗をステータスに出す。画面は閉じない。"""
        self.statusBar().showMessage(message)

    def _poll_osc(self) -> None:
        """接続状態を更新する。失敗しても起動は続ける。"""
        state = self._osc.poll()
        self.osc_label.setText(state.message)

    def _send_bool(self, name: str, value: bool) -> None:
        """真偽のパラメータを送る。"""
        error = self._osc.send_parameter(name, value)
        self.statusBar().showMessage("送信しました" if error is None else f"送信できません: {error}")

    def _send_float(self, name: str, value: float) -> None:
        """0〜1 のパラメータを送る。"""
        error = self._osc.send_parameter(name, float(value))
        self.statusBar().showMessage("送信しました" if error is None else f"送信できません: {error}")

    def _send_depth_preview(self) -> None:
        """深度プレビューのオンオフを送る。"""
        self._send_bool("PrismShot/DepthPreview", self.depth_preview.isChecked())

    def _capture(self) -> None:
        """標準カメラのシャッターを送る。"""
        error = self._osc.capture()
        self.statusBar().showMessage("撮影を送りました" if error is None else f"撮影できません: {error}")

    def _on_file(self, path: Path) -> None:
        """監視スレッドから、画像パスだけを画面側へ渡す。"""
        if is_image_path(path):
            self.arrived.emit(str(path))

    def _import_path(self, text: str) -> None:
        """新しい写真を、書き込み完了まで少し待って開く。"""
        path = Path(text)
        if not path.is_file():
            self._retry(path)
            return
        try:
            # 途中のファイルは読めないので、失敗したら待つ。
            with path.open("rb"):
                pass
        except OSError:
            self._retry(path)
            return
        self._open_path(path)
        self._refresh_gallery()

    def _retry(self, path: Path) -> None:
        """最大5回まで、ファイルの完成を待つ。"""
        if self._retries >= 5:
            return
        self._retries += 1
        QTimer.singleShot(500, lambda: self._import_path(str(path)))

    def dragEnterEvent(self, event) -> None:
        """ファイルのドロップを受ける。"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        """最初の画像を開く。"""
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if is_image_path(path):
                self._open_path(path)
                break

    def closeEvent(self, event) -> None:
        """監視を止めてから閉じる。"""
        self._watcher.stop()
        super().closeEvent(event)
