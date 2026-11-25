# stage1-container

Owner: Anna Running Rabbit

An intentionally vulnerable staff portal for the mock company Crystal Tokyo. It
is used to generate attack and normal-traffic logs for the rest of the pipeline.

**Only run this locally.** It is deliberately insecure.

## How to run

### With Docker (recommended)
 
Requires Docker Desktop to be running. From the `stage1-container` folder:
 
```bash
docker compose up --build
```
 
Open http://127.0.0.1:5000. To stop it, press `Ctrl+C`, then run:
 
```bash
docker compose down
```
 
The database is rebuilt every time the container starts, so every run starts from the same state.
 
_nginx is not set up yet; it will be added in front of the app._
 
### Without Docker (for quick testing)
 
On Windows, use **PowerShell** (not WSL). From the `app` folder:
 
```powershell
pip install flask
python seed.py
python app.py
```
 
Open http://127.0.0.1:5000. Stop the app with `Ctrl+C`. `seed.py` rebuilds the database each time it runs.
 
On macOS or Linux, use `python3` instead of `python`. If `pip install flask` fails with an `externally-managed-environment` error, install Flask in a virtual environment:
 
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask
```

## Vulnerable endpoints

| Attack | Endpoint | Weakness |
|---|---|---|
| SQL injection | `/search?q=` | User input is put directly into the SQL query; database errors are shown on the page |
| Directory traversal | `/download?file=` | The file path isn't checked, so `../` can reach files outside `files/` |
| Session hijacking | `/login`, `/profile`, `/logout` | The session ID is the MD5 of the username, never expires, is accepted in the URL (`?sid=`), and stays valid after logout |

`app/config/secrets.txt` contains **fake** credentials, planted as the directory traversal target.

## Test accounts

20 fake users (e.g. `s.moon`, `s.mercury`, `c.luna`). Each password is the username followed by `123`, e.g. `s.moon` / `s.moon123`.

## Inputs / outputs

**Input:** HTTP requests: normal browsing, or attacks sent with Burp Suite.
 
**Output:** `app.log`, with one JSON line per request. With Docker it is written to `data/live_logs/app.log` (not committed to Git); without Docker it is written to the `app` folder.
 
When running in Docker, `src_ip` is currently the Docker network's address (e.g. `172.18.0.1`) rather than the real client. This will be fixed when nginx is added.
 
| Field | Meaning |
|---|---|
| `ts` | Time of the request (UTC) |
| `src_ip` | Client IP address |
| `method`, `path`, `query`, `status` | HTTP request details |
| `session_id`, `user` | Session ID and logged-in user, if any |
| `sql` | SQL query that ran |
| `rows_returned` | Number of rows the query returned |
| `file_served` | File sent by `/download` |
| `error` | Error message, if any |