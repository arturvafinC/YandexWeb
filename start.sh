#!/bin/bash
set -e

alembic upgrade head
python scripts/seed_data.py
python run.py
