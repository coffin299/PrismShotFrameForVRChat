# SPDX-License-Identifier: Apache-2.0
"""Studio の起動。"""

from __future__ import annotations

import sys


def main() -> None:
    """画面を開く。"""
    from PySide6.QtWidgets import QApplication

    from prismshot.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    raise SystemExit(app.exec())
