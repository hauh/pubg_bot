import logging
from os import getenv

# bot
bot_token = getenv('TG_TOKEN')
log_name = 'pubg_bot.log'
admin_id = [int(i) for i in getenv('ADMIN_ID').split(',')]
battle_chat = getenv('BATTLE_CHAT_LINK')

# api

# logger
logging.basicConfig(
	format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s',
	level=logging.INFO,
	handlers=[logging.FileHandler(log_name), logging.StreamHandler()],
)
