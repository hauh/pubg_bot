"""Configuration file"""

import os
import logging
from datetime import datetime

import pytz

##############################

# bot
bot_token = os.environ['TOKEN']
proxy = os.getenv('PROXY')
debug_server = "http://localhost:7777/"

# payments
unitpay_secret = 'some_secret'  # os.environ['UNITPAY_SECRET']
unitpay_key = 'some_key'  # os.environ['UNITPAY_KEY']
unitpay_auth_params = {
	'params[projectId]': 'some_project_id',  # os.environ['UNITPAY_PROJECT_ID']
	'params[login]': 'some_login',  # os.environ['UNITPAY_EMAIL'],
	'params[secretKey]': 'some_api_key'  # os.environ['UNITPAY_API_KEY']
}
unitpay_url = f"https://unitpay.money/pay/{unitpay_key}"
unitpay_api = "https://unitpay.money/api"

# logging
os.makedirs('logs', exist_ok=True)
log_filename = f"logs/{datetime.now().strftime('%Y.%m.%d')}.log"
logging.basicConfig(
	level=logging.INFO,
	format='{asctime} - {name}.{funcName} - {levelname} - {message}',
	style='{',
	handlers=[
		logging.FileHandler(log_filename, encoding='utf-8'),
		logging.StreamHandler()
	]
)

# management
admin_id = [int(os.environ['ADMIN_ID'])]
admin_chat = admin_id[0]  # os.environ['ADMIN_CHAT']
battle_chat = 'https://t.me/snapcaster'  # os.environ['CHAT_URL']

# tournaments
timezone = pytz.timezone('Europe/Moscow')
times = {
	'slot_interval': 30,
	'close_slot': 30,
	'send_room': 15,
}
max_slots = 24
max_players = 70
enough_players = 70
bets = range(10, 101, 10)
prizes = {
	'survival_easy': {
		'kills': 0,
		'top': {
			50: 1.40
		},
	},
	'survival_medium': {
		'kills': 0,
		'top': {
			25: 2.80
		},
	},
	'survival_hard': {
		'kills': 0,
		'top': {
			10: 7.00
		},
	},
	'kills': {
		'kills': 0.70,
		'top': None,
	},
	'mixed': {
		'kills': 0.22,
		'top': {
			10: 2.50,
			25: 1.50
		},
	}
}
