from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.db import conn
from app.links import create_link, resolve_link
from app.ratelimit import check_rate_limit

app = FastAPI()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/shorten")
def shorten(request: Request, url: str):
    if not check_rate_limit(request.client.host):
        raise HTTPException(status_code=429, detail="Too many requests")
    return {"code": create_link(url)}


@app.get("/{code}")
def redirect(code: str, request: Request):
    url = resolve_link(code)
    if url is None:
        raise HTTPException(status_code=404)
    conn.execute(
        "INSERT INTO clicks (code, ts, user_agent) VALUES (?, ?, ?)",
        (code, datetime.utcnow().isoformat(), request.headers.get("user-agent")),
    )
    conn.commit()
    return RedirectResponse(url)
