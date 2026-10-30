# SPDX-License-Identifier: Apache-2.0
"""写真フォルダの列挙。"""

from __future__ import annotations

from pathlib import Path

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def vrchat_picture_dir() -> Path:
    """VRChat が写真を書く標準のフォルダ。"""
    return Path.home() / "Pictures" / "VRChat"


def list_photos(directory: Path | None = None) -> list[Path]:
    """画像を更新時刻の新しい順に返す。フォルダが無くても空リスト。"""
    folder = directory if directory is not None else vrchat_picture_dir()
    if not folder.is_dir():
        return []
    files = [
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    # 新しい写真を先に見せる。
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return files


def is_image_path(path: Path) -> bool:
    """監視で拾う拡張子か。"""
    return path.suffix.lower() in IMAGE_SUFFIXES
