"""WSGI entrypoint.

Vercel's Python runtime imports this module and serves the WSGI callable named
`app`. Deliberately not named app.py: that would shadow the `app/` package this
module imports from.
"""
from app import create_app

app = create_app()
