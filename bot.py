from logging import getLogger

from telegram import ParseMode
from telegram.ext import (
	Updater, ConversationHandler, CommandHandler,
	MessageHandler, CallbackQueryHandler, Filters
)

import config as cnf
import messages as msg
import markups as mrk
from admin import admin_handler

########################

logger = getLogger('bot')

START, MAIN = range(1, 3)


def start(update, context):
	update.effective_chat.send_message(
		msg.start,
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=mrk.start_admin
			if update.effective_user.id in cnf.admin_id
			else mrk.start_user
	)
	return 'MAIN'


def beginGame(update, context):
	update.effective_chat.send_message(
		msg.begin_game,
		parse_mode=ParseMode.MARKDOWN

	)
	return ConversationHandler.END


def profile(update, context):
	update.effective_chat.send_message(
		msg.profile,
		parse_mode=ParseMode.MARKDOWN
	)
	return ConversationHandler.END


def howItWorks(update, context):
	update.effective_chat.send_message(
		msg.how_it_works,
		parse_mode=ParseMode.MARKDOWN
	)
	return ConversationHandler.END


def about(update, context):
	update.effective_chat.send_message(
		msg.about,
		parse_mode=ParseMode.MARKDOWN
	)
	return ConversationHandler.END


def error(update, context):
	logger.error(
		"Update: {}\nError: {}, argument: {}"
			.format(update, type(context.error).__name__, context.error)
	)
	update.effective_chat.send_message(msg.error)
	return ConversationHandler.END


def stop(update, context):
	update.effective_chat.send_message(msg.stop)
	return ConversationHandler.END


def main():
	updater = Updater(
		token=cnf.bot_token,
		use_context=True,
	)
	dispatcher = updater.dispatcher

	main_handler = ConversationHandler(
		entry_points=[
			CommandHandler('start', start),
		],
		states={
			'MAIN': [
				CallbackQueryHandler(beginGame, pattern=r'^begin_game$'),
				CallbackQueryHandler(profile, pattern=r'^profile$'),
				CallbackQueryHandler(howItWorks, pattern=r'^how_it_works$'),
				CallbackQueryHandler(about, pattern=r'^about$'),
				admin_handler
			],
		},
		fallbacks=[
			CommandHandler('stop', stop),
		],
		conversation_timeout=3600
	)

	dispatcher.add_handler(main_handler)
	dispatcher.add_error_handler(error)

	logger.info('Bot started')

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
