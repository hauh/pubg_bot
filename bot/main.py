'''Main, bot starts here'''

import sys
from logging import getLogger

from telegram import ParseMode
from telegram.ext import Defaults, Updater
from telegram.error import BadRequest
from telegram.utils.request import Request

import config
import database
import texts
import jobs
import utility
import admin
import matches
import cabinet

from bot import Bot
from menu_handler import MenuHandler

########################

logger = getLogger('bot')


def start(update, context, menu):
	user_id = int(update.effective_user.id)
	username = update.effective_user.username
	if not (user := database.get_user(user_id)):
		user = database.save_user(user_id, username)
		user['balance'] = 0
		user['games_played'] = 0
	if user['banned']:
		return (texts.banned, None)
	if user['username'] != username:
		database.update_user(user_id, username=username)
		user['username'] = username
	if not user['admin'] and user_id in config.admin_id:
		database.update_user(user_id, admin=True)
		user['admin'] = True
	context.user_data.update(user)
	if user['pubg_username']:
		msg = menu['msg_registered'].format(
			user['pubg_username'], user['balance'], user['games_played'])
	else:
		msg = menu['msg']
	if user['admin']:
		return (msg, [menu['extra_buttons']['admin']] + menu['buttons'])
	return (msg, menu['buttons'])


def error(update, context):
	if update and context.user_data:
		if update.callback_query:
			try:
				update.callback_query.answer(texts.error, show_alert=True)
			except BadRequest:
				pass
		MenuHandler.send_message(
			update.effective_chat,
			context.user_data.setdefault('old_messages', []),
			*start(update, context, texts.menu)
		)
		log_entry = f"User broke down bot here: {context.user_data.get('history')}"
	else:
		log_entry = "Bot broke down!"
	logger.error(log_entry, exc_info=(type(context.error), context.error, None))


def init_menu():
	def add_buttons(menu, depth=0):
		buttons = []
		for key, next_menu in menu.get('next', {}).items():
			if 'btn' in next_menu:
				buttons.append(utility.button(key, next_menu['btn']))
			add_buttons(next_menu, depth + 1)
		if depth:
			buttons.append(back_button + (main_button if depth > 1 else []))
		menu['buttons'] = buttons
		for key, text in menu.get('extra_buttons', {}).items():
			menu['extra_buttons'][key] = utility.button(key, text)

	# adding buttons to menu
	back_button = utility.button('_back_', texts.back)
	main_button = utility.button('_main_', texts.main)
	add_buttons(texts.menu)
	texts.menu['buttons'][4][0].url = config.battle_chat

	# adding callbacks to menu
	texts.menu['callback'] = start
	admin.add_callbacks()
	matches.add_callbacks()
	cabinet.add_callbacks()


def main():
	try:
		database.prepare_DB()
	except Exception as err:  # pylint: disable=broad-except
		logger.critical(
			"Database connection failed with:",
			exc_info=(type(err), err, None)
		)
		sys.exit(-1)

	init_menu()

	updater = Updater(
		bot=Bot(
			config.bot_token,
			defaults=Defaults(parse_mode=ParseMode.MARKDOWN),
			request=Request(
				con_pool_size=10,
				proxy_url=config.proxy if config.proxy else None
			)
		),
		use_context=True
	)

	updater.dispatcher.add_handler(MenuHandler(texts.menu))
	updater.dispatcher.add_error_handler(error)
	updater.dispatcher.bot_data['debug'] = False

	updater.job_queue.run_once(jobs.restore_state, 0)
	updater.job_queue.run_repeating(jobs.check_slots_and_games, 300, first=60)

	updater.start_webhook(**config.webhook_kwargs)
	logger.info("Bot started")

	updater.idle()

	logger.info("Bot stopped")


if __name__ == '__main__':
	main()
