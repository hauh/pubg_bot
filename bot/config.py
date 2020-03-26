import logging
import pytz
from os import getenv

# bot
bot_token = getenv('TG_TOKEN')
admin_id = [int(i) for i in getenv('ADMIN_ID').split(',')]
admin_group_id = getenv('ADMIN_GROUP_ID')
battle_chat = getenv('BATTLE_CHAT_LINK')

# logger
logging.basicConfig(
	format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s',
	level=logging.INFO,
	handlers=[logging.FileHandler('pubg_bot.log'), logging.StreamHandler()],
)

# time
timezone = pytz.timezone('Europe/Moscow')
times = {
	'slot_interval': 30,
	'close_slot': 30,
	'send_room': 10,
}

# prizes
prize_structure = {
	'survival': {
		'kill': 0,
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
		'kill': 75.0,
		1: 0.0,
		2: 0.0,
		3: 0.0,
		4: 0.0,
		5: 0.0,
		6: 0.0,
		7: 0.0,
		8: 0.0,
		9: 0.0,
		10: 0.0,
	},
	'mixed': {
		'kill': 35.0,
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
