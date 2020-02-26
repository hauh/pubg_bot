from logging import getLogger

from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

import config
import texts
import buttons
import menu
import matches
import rooms
import database

########################

logger = getLogger('bot')


def error(update, context):
	logger.error(
		"Update: {}\nError: {}, argument: {}"
			.format(update, type(context.error).__name__, context.error)
	)
	update.effective_chat.send_message(texts.error)
	update.effective_chat.send_message(texts.error)
	return -1


def main():
	buttons.prepareMenu()
	database.prepareDB()

	updater = Updater(
		token=config.bot_token,
		use_context=True,
	)
	dispatcher = updater.dispatcher

	dispatcher.add_handler(CommandHandler('start', menu.mainMenu))
	dispatcher.add_handler(CallbackQueryHandler(menu.mainMenu, pattern=r'^main$'))
	dispatcher.add_handler(CallbackQueryHandler(menu.back, pattern=r'^back$'))
	dispatcher.add_handler(matches.handler)
	dispatcher.add_handler(rooms.handler)
	dispatcher.add_handler(menu.MenuHandler(texts.main_menu))
	dispatcher.add_error_handler(error)

	logger.info('Bot started')

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
