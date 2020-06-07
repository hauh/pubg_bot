'''Configuration file'''

import os
import logging
from datetime import datetime

import pytz

##############################

# bot
bot_token = os.environ['TG_TOKEN']
webhook_kwargs = {
	'listen': '0.0.0.0',
	'port': 8443,
	'url_path': bot_token,
	'key': os.getenv('SSL_KEY'),
	'cert': os.getenv('SSL_CERT'),
	'webhook_url': f"{os.getenv('SERVER_ADDRESS')}:8443/{bot_token}",
	# 'allowed_updates': ['message', 'callback_query']  # bugged in ptb
}
proxy = os.getenv('PROXY')
db_url = os.environ['DATABASE']
debug_chat = os.environ['DEBUG_CHAT']

# qiwi
qiwi_token = os.environ['QIWI_TOKEN']
qiwi_phone = os.environ['QIWI_PHONE']

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
if admin_id := os.getenv('ADMIN_ID'):
	admin_id = [int(i) for i in admin_id.split(',')]
admin_group_id = os.environ['ADMIN_GROUP_ID']
battle_chat = os.environ['CHAT_URL']

# tournaments
timezone = pytz.timezone('Europe/Moscow')
times = {
	'slot_interval': 30,
	'close_slot': 30,
	'send_room': 15,
}
max_players = 70
enough_players = 70
bets = {
	'min': 10,
	'max': 100,
	'step': 10
}
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
