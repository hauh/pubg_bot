from logging import getLogger

from telegram import ParseMode
from telegram.ext import (
	Updater, ConversationHandler, CommandHandler,
	MessageHandler, CallbackQueryHandler, Filters
)

import config as cnf
import texts as txt
import menu as menu

########################

logger = getLogger('bot')


def start(update, context):
	if update.callback_query:
		update.callback_query.message.delete()
	update.effective_chat.send_message(
		txt.menu['msg'],
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=menu.createKeyboard(txt.menu)
	)
	context.user_data['conv_history'] = ['main']
	return 'main'


def error(update, context):
	logger.error(
		"Update: {}\nError: {}, argument: {}"
			.format(update, type(context.error).__name__, context.error)
	)
	update.effective_chat.send_message(txt.error)
	return ConversationHandler.END


def main():
	updater = Updater(
		token=cnf.bot_token,
		use_context=True,
	)
	dispatcher = updater.dispatcher

	dispatcher.add_handler(CommandHandler('start', start))
	dispatcher.add_handler(menu.MenuHandler(txt.menu))
	dispatcher.add_error_handler(error)

	logger.info('Bot started')

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
