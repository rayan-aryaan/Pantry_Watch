"""PantryWatch: a tiny REST API that tracks pantry items and flags what expires soon."""
from datetime import date, timedelta

from flask import Flask, jsonify, request

app = Flask(__name__)
ITEMS: dict[int, dict] = {}
_next_id = 1


def days_left(expires: date, today: date | None = None) -> int:
    return (expires - (today or date.today())).days


def status_for(days: int) -> str:
    if days < 0:
        return "expired"
    if days <= 3:
        return "use_soon"
    return "fresh"


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/items")
def add_item():
    global _next_id
    body = request.get_json(silent=True) or {}
    name, expires = body.get("name"), body.get("expires")
    if not name or not expires:
        return jsonify(error="name and expires (YYYY-MM-DD) are required"), 400
    try:
        exp = date.fromisoformat(expires)
    except ValueError:
        return jsonify(error="expires must be YYYY-MM-DD"), 400
    item = {"id": _next_id, "name": name, "expires": exp.isoformat()}
    ITEMS[_next_id] = item
    _next_id += 1
    return jsonify(item), 201


@app.get("/items")
def list_items():
    out = []
    for it in ITEMS.values():
        d = days_left(date.fromisoformat(it["expires"]))
        out.append({**it, "days_left": d, "status": status_for(d)})
    out.sort(key=lambda x: x["days_left"])
    return jsonify(out)


@app.get("/items/expiring")
def expiring():
    window = int(request.args.get("days", 3))
    cutoff = date.today() + timedelta(days=window)
    hits = [i for i in ITEMS.values() if date.fromisoformat(i["expires"]) <= cutoff]
    return jsonify(hits)
