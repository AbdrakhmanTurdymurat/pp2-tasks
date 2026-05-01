# TSIS 3 — Snake Game

## Run
```bash
pip install -r requirements.txt
python main.py
```

## PostgreSQL
The game creates these tables automatically:
- `players`
- `game_sessions`

Default DB settings:
- host: `localhost`
- port: `5432`
- dbname: `postgres`
- user: `postgres`
- password: `0`

Override with:
- `PGHOST`
- `PGPORT`
- `PGDATABASE`
- `PGUSER`
- `PGPASSWORD`

## Notes
- Username is typed on the main menu.
- Results are saved automatically after game over.
- If PostgreSQL is unavailable, the game still runs.
