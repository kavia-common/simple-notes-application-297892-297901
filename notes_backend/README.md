# Notes Backend (FastAPI)

This service exposes a Notes CRUD API.

- ASGI app: src.api.main:app
- Default port: 3001 (configure in your process manager or uvicorn run command)
- Health endpoint: GET /

Environment
- DATABASE_URL: PostgreSQL connection string (optional)
  Defaults to postgresql://postgres:postgres@localhost:5001/postgres

Run locally
- Install: pip install -r requirements.txt
- Start: uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload

CORS
- Allows http://localhost:3000 and http://127.0.0.1:3000 by default.

Notes
- DB engine and tables are created lazily on first DB access to avoid startup failures when DB is unavailable.
