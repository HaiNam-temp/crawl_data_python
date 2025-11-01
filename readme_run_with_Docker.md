Run the project with Docker

This document explains how to build and run the Sophie Chatbot project using Docker and Docker Compose. It assumes you have Docker and Docker Compose installed on your machine.

Contents
- Build and run with docker-compose
- Environment variables and volumes
- Starting the optional DB writer
- Inspecting the SQLite database and basic maintenance
- Troubleshooting tips

## Build and run (recommended)

From the repository root (where docker-compose.yml is located), run:

1. Build and start the stack:

   docker compose up --build

   This will build the image and start two services:
   - app — the FastAPI backend, exposed at http://localhost:8010
   - frontend — a tiny static HTTP server, exposed at http://localhost:3000

2. Stop the stack:

   docker compose down

If you only want to start the services without rebuilding, run:

   docker compose up

## Ports
- Backend (FastAPI / Uvicorn): 8010 -> localhost:8010
- Frontend (static server): 3000 -> localhost:3000

## Persistent data (SQLite)

The SQLite file used by the app is configured by DB_PATH in backend/config.py. The compose file sets DB_PATH=/data/chatbot_database.db and mounts a named volume sophie_data at /data in the container. This keeps the DB file persistent across container restarts.

If you prefer to keep the DB file on your host filesystem (for easy inspection), modify docker-compose.yml and replace the data volume with a bind mount, for example:

    volumes:
      - ./:/app:cached
      - ./data:/data

That will place chatbot_database.db in ./data on the host.

## Environment variables

- DB_PATH — path to SQLite DB inside the container (default in compose: /data/chatbot_database.db). You can override other behaviour by setting environment variables in docker-compose.yml or via .env when running docker-compose.

## Start the DB writer (optional but recommended for crawling)

The project includes a simple background DB writer (backend/db_writer.py) that serializes write batches to avoid SQLite contention. The writer is not started automatically by default. To enable it, you can:

1. Edit main.py and call start_db_writer() in the startup event, or
2. Start it manually from a Python console inside the container.

Example (auto-start in main.py):

    from backend.db_writer import start_db_writer

    @app.on_event("startup")
    async def startup_event():
        init_database()
        start_db_writer()

If you prefer the manual approach, run an interactive shell in the container and start the writer:

    docker compose exec app pwsh
    python -c "from backend.db_writer import start_db_writer; start_db_writer(); print('started')"

## Inspecting and maintaining the SQLite DB

I added a small helper module backend/db_maintenance.py with these functions:
- integrity_check(db_path) — runs PRAGMA integrity_check; and returns (ok, message)
- backup_db(db_path, backup_path=None) — uses the sqlite3 backup API to create a binary backup
- remove_journal_if_exists(db_path) — removes <db>-journal file if present

You can use them from inside the container. Example:

    docker compose exec app pwsh
    python -c "from backend.db_maintenance import integrity_check, backup_db; print(integrity_check('/data/chatbot_database.db')); print(backup_db('/data/chatbot_database.db'))"

On the host you can also use the sqlite3 CLI if you have it installed:

    sqlite3 data/chatbot_database.db ".schema"
    sqlite3 data/chatbot_database.db "pragma integrity_check;"

## Logs and debugging

- To see backend logs:

    docker compose logs -f app

- To see frontend logs:

    docker compose logs -f frontend

If you enabled the DB writer or are using the immediate-write fallback, insert operations are logged per-product. Watch the app logs for lines like:

- DBWriter: inserted product '...' url=...
- Inserted product '...' url=...

If you notice many OperationalError: database is locked messages, consider enabling the DB writer or switching to a server database (Postgres/MySQL) for heavier concurrent writes.

## Troubleshooting build issues

- Some dependencies in requirements.txt (e.g., chromadb, langchain-chroma, selenium and drivers) require additional system-level libraries or a browser driver. If pip install -r requirements.txt fails during image build, collect the error and we can add the required apt packages into the Dockerfile. Typical additions include: libpq-dev, libffi-dev, libssl-dev, build-essential, and browser dependencies for selenium.

- The included Dockerfile performs a permissive pip install (it may allow the build to continue if some packages fail). For production, fix package installation and remove permissive behavior so the build fails loudly on missing dependencies.

## Quick commands summary

Build and run:

    docker compose up --build

Stop and remove containers:

    docker compose down

Inspect backend logs:

    docker compose logs -f app

Enter app container shell:

    docker compose exec app pwsh

## Next steps
- If you want, I can:
  - Auto-start the DB writer at app startup.
  - Replace the named volume with a host bind-mount in docker-compose.yml.
  - Harden the Dockerfile to ensure all requirements.txt packages install cleanly (add missing system libs and browser drivers).

Feel free to tell me which of the above you'd like me to do next and I'll apply the changes.
