from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import psycopg2

from config import DB_CONFIG


@contextmanager
def get_conn():
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id SERIAL PRIMARY KEY,
                    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
                    score INTEGER NOT NULL,
                    level_reached INTEGER NOT NULL,
                    played_at TIMESTAMP DEFAULT NOW()
                );
            """)


def get_or_create_player_id(username: str) -> Optional[int]:
    username = (username or "Player").strip()[:50] or "Player"
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM players WHERE username = %s;", (username,))
                row = cur.fetchone()
                if row:
                    return int(row[0])
                cur.execute(
                    "INSERT INTO players (username) VALUES (%s) RETURNING id;",
                    (username,),
                )
                return int(cur.fetchone()[0])
    except Exception:
        return None


def save_game_session(username: str, score: int, level_reached: int) -> bool:
    player_id = get_or_create_player_id(username)
    if player_id is None:
        return False
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO game_sessions (player_id, score, level_reached)
                    VALUES (%s, %s, %s);
                    """,
                    (player_id, int(score), int(level_reached)),
                )
        return True
    except Exception:
        return False


def get_personal_best(username: str) -> int:
    username = (username or "Player").strip()[:50] or "Player"
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(MAX(gs.score), 0)
                    FROM game_sessions gs
                    JOIN players p ON p.id = gs.player_id
                    WHERE p.username = %s;
                    """,
                    (username,),
                )
                row = cur.fetchone()
                return int(row[0] or 0)
    except Exception:
        return 0


def get_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT p.username, gs.score, gs.level_reached, gs.played_at
                    FROM game_sessions gs
                    JOIN players p ON p.id = gs.player_id
                    ORDER BY gs.score DESC, gs.level_reached DESC, gs.played_at ASC
                    LIMIT %s;
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
                return [
                    {
                        "username": username,
                        "score": int(score),
                        "level_reached": int(level_reached),
                        "played_at": played_at,
                    }
                    for username, score, level_reached, played_at in rows
                ]
    except Exception:
        return []
