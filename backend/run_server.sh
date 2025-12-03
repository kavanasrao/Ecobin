#!/bin/bash
cd /app/backend
export PYTHONUNBUFFERED=1
exec /root/.venv/bin/python server.py
