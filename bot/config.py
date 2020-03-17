import logging
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
	handlers=[logging.FileHandler('../pubg_bot.log'), logging.StreamHandler()],
)

# prizes
prize_structure = {
	'survival': {
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
