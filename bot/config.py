import logging
from os import getenv

# bot
bot_token = getenv('TG_TOKEN')
admin_id = [int(i) for i in getenv('ADMIN_ID').split(',')]
battle_chat = getenv('BATTLE_CHAT_LINK')

# logger
logging.basicConfig(
	format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s',
	level=logging.INFO,
	handlers=[logging.FileHandler('../pubg_bot.log'), logging.StreamHandler()],
)
