---
kind: error_handling
name: Simple Python Error Handling in Atlas Panel and Mailer Services
category: error_handling
scope:
    - '**'
source_files:
    - docker/panel/app/main.py
    - docker/panel/app/db.py
    - docker/mailer/mailer.py
    - docker/mailer/send_email.py
---

## What system/approach is used

The repository contains two small Python services under `docker/` — a FastAPI admin panel (`docker/panel/app`) and a standalone SMTP mailer (`docker/mailer`). Error handling is minimal and idiomatic Python, with no custom error types, no centralized exception hierarchy, and no structured logging framework.

- **FastAPI panel**: Uses FastAPI's built-in `HTTPException` for request-level errors (404s) and relies on FastAPI's default exception-to-JSON conversion for unhandled exceptions. A simple HTTP middleware enforces authentication by redirecting unauthenticated requests to `/login`.
- **Mailer service**: Built on `http.server.BaseHTTPRequestHandler`, returns plain JSON responses with an explicit `{"success": bool, "error": str}` envelope. Errors are caught with broad `except Exception` blocks and translated into 500 status codes.
- **Database layer**: Uses raw `psycopg2` connections wrapped in a `contextmanager` that guarantees `conn.close()`; database exceptions propagate up to the caller without wrapping.

There is no `errors/` package, no sentinel/error-code constants module, no `panic`/`recover` equivalent (Python), and no global error handler beyond FastAPI's defaults.

## Key files and packages

- `docker/panel/app/main.py` — FastAPI app entry point; defines routes, auth middleware, and raises `HTTPException(404)` when requested resources (monthly report, call detail) are not found.
- `docker/panel/app/db.py` — Database connection helper using `psycopg2`; wraps connection lifecycle in a `@contextmanager` so connections are always closed, but does not catch or translate DB exceptions.
- `docker/panel/app/config.py` — Loads configuration (DB credentials, panel password); missing config values would cause runtime failures at startup/connection time.
- `docker/mailer/mailer.py` — Standalone HTTP server exposing `/send`; validates input JSON, catches `json.JSONDecodeError` explicitly, and catches all other exceptions via `except Exception as exc` to return a JSON error payload.
- `docker/mailer/send_email.py` — CLI wrapper that calls `main()` and exits via `raise SystemExit(main())`.

## Architecture and conventions

1. **Per-route error shaping** — Each endpoint handles its own failure path locally rather than delegating to a central handler. In `main.py`, missing resources raise `HTTPException(404)` directly from the route; in `mailer.py`, malformed input returns 400 with a JSON body, while SMTP/network failures return 500 with the exception message.
2. **JSON error envelope in the mailer** — The mailer consistently returns `{"success": False, "error": <message>}` for both configuration errors (missing `SMTP_PASS`) and runtime exceptions, giving callers a uniform shape to inspect.
3. **Authentication as a middleware guard** — Auth failures are not raised as exceptions; they are handled by returning `RedirectResponse("/login", status_code=302)`. This keeps the rest of the route handlers free of auth checks.
4. **Login error signaling via query string** — Failed login redirects to `/login?error=1`, letting the template render a user-facing error message without using HTTP status codes.
5. **Resource cleanup via context managers** — DB connections are acquired through `get_conn()`, which uses `try/finally` to ensure `conn.close()` runs even if a query raises. No custom exception type is introduced around psycopg2 errors.
6. **No global exception-to-response mapping** — Only FastAPI's default exception handler exists; there is no `@app.exception_handler` override, no structured error response model, and no log aggregation for errors.
7. **Process exit on CLI errors** — Scripts under `docker/scripts/` and `docker/mailer/send_email.py` terminate via `raise SystemExit(main())`, treating `main()`'s return value as the process exit code.

## Conventions and constraints observed

- **FastAPI routes use `HTTPException` for client/server errors** — Missing-resource cases return 404 via `raise HTTPException(404)`; there is no custom error subclass or unified error DTO.
- **Mailer errors are returned as JSON, not logged** — The mailer writes error messages into the response body (`{"error": str(exc)}`) and prints request logs via an overridden `log_message`; there is no file-based or structured logger configured.
- **Configuration errors short-circuit early** — The mailer checks `if not SMTP_PASS` before attempting SMTP and returns a descriptive error; missing DB credentials would surface as a psycopg2 connection exception.
- **Auth bypasses normal routing** — The `auth_middleware` intercepts every request before it reaches a route, redirecting unauthenticated users instead of raising an exception, which means downstream handlers never see an auth-failure signal.
- **No retry, timeout, or circuit-breaker logic** — SMTP calls use a fixed 30-second `smtplib.SMTP` timeout; failed sends are surfaced as 500 errors with no retry policy.
- **No tests or error-case fixtures exist** — There are no test files in this workspace that assert error behavior, so these patterns are informal conventions rather than enforced requirements.