'''Main, bot starts here'''

import sys
from logging import getLogger

from telegram import ParseMode
from telegram.ext import Defaults, Updater
from telegram.error import BadRequest

import config
import database
import texts
import jobs
import utility
import admin
import matches
import cabinet

from menu_handler import MenuHandler

########################

logger = getLogger('bot')


def start(update, context, menu):
	user_id = int(update.effective_user.id)
	username = update.effective_user.username
	if not (user := database.get_user(id=user_id)):
		user = database.save_user(user_id, username)
	if user['banned']:
		return (texts.banned, None)
	if 'balance' not in context.user_data:
		user['balance'] = database.get_balance(user_id)
	if user['username'] != username:
		database.update_user(user_id, username=username)
		user['username'] = username
	if not user['admin'] and user_id in config.admin_id:
		database.update_user(user_id, admin=True)
		user['admin'] = True
	context.user_data.update(user)
	if user['admin']:
		return (menu['msg'], [menu['extra_buttons']['admin']] + menu['buttons'])
	return (menu['msg'], menu['buttons'])


def error(update, context):
	if update and context.user_data:
		if update.callback_query:
			try:
				update.callback_query.answer(texts.error, show_alert=True)
			except BadRequest:
				pass
		MenuHandler.send_message(
			update, *start(update, context, texts.menu),
			context.user_data.setdefault('old_messages', [])
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
		token=config.bot_token,
		use_context=True,
		defaults=Defaults(parse_mode=ParseMode.MARKDOWN),
		request_kwargs=dict(proxy_url=config.proxy) if config.proxy else None
	)

	updater.dispatcher.add_handler(MenuHandler(texts.menu))
	updater.dispatcher.add_error_handler(error)

	updater.job_queue.run_once(jobs.restore_state, 0)
	updater.job_queue.run_repeating(jobs.check_slots_and_games, 5, first=1)

	logger.info("Bot started")

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
