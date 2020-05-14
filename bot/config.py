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

# slots
timezone = pytz.timezone('Europe/Moscow')
times = {
	'slot_interval': 30,
	'close_slot': 30,
	'send_room': 15,
}
max_players = 70
enough_players = 70

# prizes
prize_structure = {
	'survival': {
		'kills': 0,
		1: 10.0,
		2: 9.0,
		3: 8.0,
		4: 6.0,
		5: 6.0,
		6: 6.0,
		7: 6.0,
		8: 6.0,
		9: 6.0,
		10: 6.0,
	},
	'kills': {
		'kills': 70.0,
	},
	'mixed': {
		'kills': 35.0,
		1: 5.0,
		2: 4.5,
		3: 4.0,
		4: 3.0,
		5: 3.0,
		6: 3.0,
		7: 3.0,
		8: 3.0,
		9: 3.0,
		10: 3.0,
	}
}
