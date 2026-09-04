"""WSGI entrypoint.

Vercel's Python runtime imports this module and serves the WSGI callable named
`app`. Deliberately not named app.py: that would shadow the `app/` package this
module imports from.
"""
from app import create_app
from flask import request, jsonify

app = create_app()


@app.route("/__debug", defaults={"p": ""})
@app.route("/__debug/<path:p>")
def __debug(p):
    return jsonify({
        "path": request.path,
        "script_root": request.script_root,
        "routes": sorted(str(r) for r in app.url_map.iter_rules()),
    })