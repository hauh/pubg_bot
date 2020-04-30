import os
import logging
import pytz


# bot
bot_token = os.getenv('TG_TOKEN')
admin_id = [int(i) for i in os.getenv('ADMIN_ID').split(',')]
admin_group_id = os.getenv('ADMIN_GROUP_ID')
battle_chat = os.getenv('BATTLE_CHAT_LINK')
db_url = os.getenv('HEROKU_DB')

# qiwi
qiwi_token = os.getenv('QIWI_TOKEN')
qiwi_phone = os.getenv('QIWI_PHONE')
qiwi_url = 'https://qiwi.com'

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
		'kills': 75.0,
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
