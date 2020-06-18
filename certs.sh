#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"
rm -rf certs
mkdir certs
cp -L /etc/letsencrypt/live/bot.pubglik.ru/*.pem -t certs/
chown -R tg_bot certs
