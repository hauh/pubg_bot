import sys
from logging import getLogger

from telegram import ParseMode
from telegram.ext import (
	Defaults, Filters, Updater, CallbackQueryHandler, CommandHandler
)


import config
import database
import texts
import buttons
import menu
import matches
import rooms
import profile
import admin

########################

logger = getLogger('bot')


def mainMenu(update, context):
	user_id = int(update.effective_user.id)
	chat_id = int(update.effective_chat.id)
	username = update.effective_user.username
	user = database.getUser(user_id)
	if not user or user['chat_id'] != chat_id or user['username'] != username:
		database.saveUser(user_id, chat_id, username)
		user = database.getUser(user_id)
	context.user_data.update(user)
	return (
		texts.menu['msg'],
		texts.menu['buttons'] if user_id in config.admin_id
			else texts.menu['buttons'][1:]
	)


def error(update, context):
	logger.error(
		"Update: {}\nError: {}, argument: {}"
			.format(update, type(context.error).__name__, context.error)
	)
	context.chat_data['old_messages'].append(
		update.effective_chat.send_message(texts.error))
	return mainMenu(update, context)


def main():
	try:
		database.prepareDB()
	except Exception:
		logger.critical("Database required!")
		sys.exit(-1)

	buttons.generateButtons(texts.menu)
	buttons.updateSpecialButtons()

	updater = Updater(
		token=config.bot_token,
		use_context=True,
		defaults=Defaults(parse_mode=ParseMode.MARKDOWN)
	)
	dispatcher = updater.dispatcher

	dispatcher.add_handler(menu.MenuHandler(
		texts.menu,
		[
			matches.callbacks,
			profile.callbacks,
			{'main': mainMenu},
		])
	)
	# dispatcher.add_handler(CallbackQueryHandler(menu.back, pattern=r'^back$'))
	dispatcher.add_error_handler(error)

	logger.info("Bot started")

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
