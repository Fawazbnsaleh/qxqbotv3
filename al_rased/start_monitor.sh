#!/bin/bash
# Start Telethon Monitor Service

cd "$(dirname "$0")"
source venv/bin/activate
python3 -m services.telethon_monitor.monitor
