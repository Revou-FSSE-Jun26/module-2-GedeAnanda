"""Vercel serverless entrypoint.

Vercel looks for a WSGI callable named `app` in this module and serves every
request routed here (see vercel.json) through it.
"""
import os
import sys

# Make the project root importable when Vercel executes this file from api/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

app = create_app()
