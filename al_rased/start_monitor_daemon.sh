#!/bin/bash
# Run Telethon Monitor as a background daemon

cd "$(dirname "$0")"
source venv/bin/activate

# Create log directory
mkdir -p logs

# Run in background with nohup
nohup python3 -m services.telethon_monitor.monitor > logs/monitor.log 2>&1 &

echo "Monitor started in background. PID: $!"
echo "Log file: al_rased/logs/monitor.log"
echo "To stop: kill $!"
