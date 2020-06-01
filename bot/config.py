'''Configuration file'''

import os
import logging
from datetime import datetime

import pytz

##############################

# bot
bot_token = os.environ['TG_TOKEN']
if admin_id := os.getenv('ADMIN_ID'):
	admin_id = [int(i) for i in admin_id.split(',')]
admin_group_id = os.environ['ADMIN_GROUP_ID']
admin_name = os.environ['ADMIN_NAME']
proxy = os.getenv('PROXY')
db_url = os.environ['DATABASE']
battle_chat = os.environ['CHAT_URL']

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

# slots and games settings
timezone = pytz.timezone('Europe/Moscow')
times = {
	'slot_interval': 30,
	'close_slot': 30,
	'send_room': 15,
}
max_players = 70
enough_players = 70
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
