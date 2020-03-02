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


def error(update, context):
	logger.error(
		"Update: {}\nError: {}, argument: {}"
			.format(update, type(context.error).__name__, context.error)
	)
	update.effective_chat.send_message(texts.error)
	return menu.mainMenu(update, context)


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

	dispatcher.add_handler(
		CommandHandler('start', menu.mainMenu, filters=Filters.private))
	dispatcher.add_handler(CallbackQueryHandler(menu.mainMenu, pattern=r'^main$'))
	dispatcher.add_handler(matches.handler)
	dispatcher.add_handler(rooms.handler)
	dispatcher.add_handler(profile.handler)
	dispatcher.add_handler(admin.handler)
	dispatcher.add_handler(menu.MenuHandler(texts.menu))
	dispatcher.add_handler(CallbackQueryHandler(menu.back, pattern=r'^back$'))
	dispatcher.add_error_handler(error)

	logger.info("Bot started")

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
