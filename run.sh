#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"
source "venv/bin/activate"
source "./env"
python3 -m "pubglik" &
