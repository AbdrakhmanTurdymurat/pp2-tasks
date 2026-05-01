from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_SETTINGS = {
    "sound_enabled": True,
    "car_color": "Red",
    "difficulty": "Normal",
}

DEFAULT_LEADERBOARD: list[dict[str, Any]] = []

def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_settings(path: Path) -> dict[str, Any]:
    data = _read_json(path, DEFAULT_SETTINGS.copy())
    result = DEFAULT_SETTINGS.copy()
    if isinstance(data, dict):
        result.update({k: data.get(k, v) for k, v in DEFAULT_SETTINGS.items()})
    return result

def save_settings(path: Path, settings: dict[str, Any]) -> None:
    merged = DEFAULT_SETTINGS.copy()
    merged.update(settings)
    _write_json(path, merged)

def load_leaderboard(path: Path) -> list[dict[str, Any]]:
    data = _read_json(path, DEFAULT_LEADERBOARD.copy())
    if isinstance(data, list):
        clean: list[dict[str, Any]] = []
        for item in data:
            if isinstance(item, dict):
                clean.append({
                    "name": str(item.get("name", "Player"))[:18],
                    "score": int(item.get("score", 0)),
                    "distance": int(item.get("distance", 0)),
                    "coins": int(item.get("coins", 0)),
                    "date": str(item.get("date", ""))[:32],
                })
        return clean
    return []

def save_leaderboard(path: Path, leaderboard: list[dict[str, Any]]) -> None:
    leaderboard = sorted(
        leaderboard,
        key=lambda x: (int(x.get("score", 0)), int(x.get("distance", 0))),
        reverse=True,
    )[:10]
    _write_json(path, leaderboard)

def record_score(path: Path, entry: dict[str, Any]) -> list[dict[str, Any]]:
    board = load_leaderboard(path)
    board.append({
        "name": str(entry.get("name", "Player"))[:18],
        "score": int(entry.get("score", 0)),
        "distance": int(entry.get("distance", 0)),
        "coins": int(entry.get("coins", 0)),
        "date": str(entry.get("date", ""))[:32],
    })
    board = sorted(board, key=lambda x: (x["score"], x["distance"]), reverse=True)[:10]
    save_leaderboard(path, board)
    return board
