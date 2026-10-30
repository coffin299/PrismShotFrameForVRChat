# SPDX-License-Identifier: Apache-2.0
"""VRChat の OSC と OSCQuery。"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

OSC_HOST = "127.0.0.1"
OSC_PORT = 9000
_PORT_PATTERN = re.compile(r"OSCQuery on (\d+)")


@dataclass
class ConnectionState:
    """接続の表示に使う状態。"""

    connected: bool
    has_shot: bool
    message: str


def vrchat_log_dir() -> Path:
    """VRChat のログフォルダ。"""
    return Path.home() / "AppData" / "LocalLow" / "VRChat" / "VRChat"


def latest_log_text(folder: Path | None = None) -> str:
    """最新ログの末尾だけを読む。フォルダが無くても空文字。"""
    directory = folder if folder is not None else vrchat_log_dir()
    if not directory.is_dir():
        return ""
    logs = list(directory.glob("output_log*.txt"))
    if not logs:
        return ""
    newest = max(logs, key=lambda path: path.stat().st_mtime)
    with newest.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(max(0, size - 262144))
        data = handle.read()
    return data.decode("utf-8", errors="ignore")


def parse_oscquery_port(text: str) -> int | None:
    """ログに出た最後の OSCQuery ポートを返す。"""
    found = _PORT_PATTERN.findall(text)
    if not found:
        return None
    return int(found[-1])


def fetch_oscquery(port: int, timeout: float = 1.5) -> dict:
    """localhost の OSCQuery から JSON を取る。"""
    request = urllib.request.Request(
        f"http://{OSC_HOST}:{port}/",
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("OSCQuery の応答がオブジェクトではありません")
    return payload


def tree_has_shot(node: object, trail: str = "") -> bool:
    """パラメータ木に PrismShot/Enable があるか。"""
    if not isinstance(node, dict):
        return False
    contents = node.get("CONTENTS")
    if not isinstance(contents, dict):
        return False
    for key, child in contents.items():
        path = f"{trail}/{key}" if trail else str(key)
        # スラッシュ区切りがネストされる場合と、1つのキーになる場合の両方。
        if path.endswith("PrismShot/Enable") or key == "Enable" and trail.endswith("PrismShot"):
            return True
        if tree_has_shot(child, path):
            return True
    return False


class OscController:
    """送信失敗でもプロセスを落とさない OSC クライアント。"""

    def __init__(self) -> None:
        self._client = None

    def poll(self, log_folder: Path | None = None) -> ConnectionState:
        """ログと OSCQuery から接続状態を作る。"""
        try:
            port = parse_oscquery_port(latest_log_text(log_folder))
            if port is None:
                return ConnectionState(False, False, "VRChat の OSCQuery が見つかりません")
            tree = fetch_oscquery(port)
            if tree_has_shot(tree):
                return ConnectionState(True, True, f"Shot に接続しました（OSCQuery {port}）")
            return ConnectionState(True, False, f"VRChat には接続しましたが Shot がありません（{port}）")
        except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
            return ConnectionState(False, False, f"未接続: {exc.__class__.__name__}")

    def send_parameter(self, name: str, value: object) -> str | None:
        """アバターパラメータを送る。失敗時はメッセージを返す。"""
        try:
            self._ensure_client()
            self._client.send_message(f"/avatar/parameters/{name}", value)
        except Exception as exc:  # 送信先が無くても画面に残すだけにする。
            return exc.__class__.__name__
        return None

    def capture(self) -> str | None:
        """標準カメラを写真モードにしてシャッターを送る。"""
        try:
            self._ensure_client()
            # 公式のユーザーカメラ。写真モードにしてから撮影する。
            self._client.send_message("/usercamera/Mode", 1)
            self._client.send_message("/usercamera/Capture", True)
        except Exception as exc:
            return exc.__class__.__name__
        return None

    def _ensure_client(self) -> None:
        """UDP クライアントを遅延作成する。"""
        if self._client is None:
            from pythonosc.udp_client import SimpleUDPClient

            self._client = SimpleUDPClient(OSC_HOST, OSC_PORT)
