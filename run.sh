#!/bin/bash
sudo docker compose up -d
nohup python3 lib/tg_bot_service.py > tg_bot_output.log &
nohup sudo python3 lib/watchdog_service.py > watchdog_output.log &