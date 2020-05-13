'''Configuration file'''

import os
import logging
import pytz


# bot
bot_token = os.environ['TG_TOKEN']
if admin_id := os.getenv('ADMIN_ID'):
	admin_id = [int(i) for i in admin_id.split(',')]
admin_group_id = os.environ['ADMIN_GROUP_ID']
battle_chat = os.environ['BATTLE_CHAT_LINK']
db_url = os.getenv('HEROKU_DB')
proxy = os.getenv('PROXY')
admin_name = os.environ['ADMIN_NAME']

# qiwi
qiwi_token = os.environ['QIWI_TOKEN']
qiwi_phone = os.environ['QIWI_PHONE']

# logger
logging.basicConfig(
	level=logging.INFO,
	format='{asctime} - {name}.{funcName} - {levelname} - {message}',
	style='{',
	handlers=[
		logging.FileHandler('pubg_bot.log', encoding='utf-8'),
		logging.StreamHandler()
	]
)

# slots
timezone = pytz.timezone('Europe/Moscow')
times = {
	'slot_interval': 5,
	'close_slot': 2,
	'send_room': 1,
}
max_players = 4
enough_players = 4

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
