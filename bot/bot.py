import sys
from logging import getLogger

from telegram import ParseMode, InlineKeyboardMarkup
from telegram.ext import Defaults, Updater, Filters, CallbackQueryHandler

import config
import database
import texts
import jobs
import utility
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
	if user_id in config.admin_id:
		user['admin'] = True
	context.user_data.update(user)
	return (
		menu['msg'],
		menu['buttons'] if user['admin'] else menu['buttons'][1:]
	)


def error(update, context):
	logger.error(
		f"User chat history: {context.user_data.get('history')}",
		exc_info=(type(context.error), context.error, None)
	)
	# if update.callback_query and update.callback_query.id != 0:
	try:
		update.callback_query.answer(texts.error, show_alert=True)
	except AttributeError:
		context.user_data.setdefault('old_messages', []).append(
			update.effective_chat.send_message(texts.error))


def gotoAdmin(update, context):
	text, buttons = admin.manageMatches(
		update, context, texts.menu['next']['admin']['next']['manage_matches'])
	context.user_data['history'] = ['manage_matches']
	if text:
		old_messages = context.user_data.setdefault('old_messages', [])
		MenuHandler.cleanChat(old_messages)
		old_messages.append(
			update.effective_user.send_message(
				text, reply_markup=InlineKeyboardMarkup(buttons))
		)


def main():
	try:
		database.prepare_DB()
	except Exception as err:
		logger.critical(
			"Database connection failed with:",
			exc_info=(type(err), err, None)
		)
		sys.exit(-1)

	utility.add_buttons_to_menu()
	import admin
	texts.menu['callback'] = start

	updater = Updater(
		token=config.bot_token,
		use_context=True,
		defaults=Defaults(parse_mode=ParseMode.MARKDOWN)
	)

	# updater.job_queue.run_repeating(jobs.checkSlots, 10, first=0)

	updater.dispatcher.add_handler(MenuHandler(texts.menu))
	updater.dispatcher.add_handler(
		CallbackQueryHandler(gotoAdmin, pattern='manage_matches'))
	updater.dispatcher.add_error_handler(error)

	logger.info("Bot started")

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
