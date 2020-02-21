from logging import getLogger

from telegram import ParseMode
from telegram.ext import (
	Updater, ConversationHandler, CommandHandler,
	MessageHandler, CallbackQueryHandler, Filters
)

import config as cnf
import markups as mrk
import texts as txt
import common
from admin import admin_handler

########################

logger = getLogger('bot')

END, MAIN, HOW, ABOUT = range(-1, 3)


def start(update, context):
	update.effective_chat.send_message(
		txt.main['message'],
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=mrk.main_menu_admin
			if update.effective_user.id in cnf.admin_id
			else mrk.main_menu_user
	)
	context.user_data['main_level'] = MAIN
	return MAIN


reply_args = {
	'how'	: (HOW, txt.main['buttons']['how']['message'], mrk.how),
	'about'	: (ABOUT, txt.main['buttons']['about']['message'], mrk.how),
}
common.reply_args = reply_args


def back(update, context):
	return start(update, context)


def again(update, context):
	return start(update, context)


def error(update, context):
	logger.error(
		"Update: {}\nError: {}, argument: {}"
			.format(update, type(context.error).__name__, context.error)
	)
	update.effective_chat.send_message(txt.error)
	return END


def stop(update, context):
	update.effective_chat.send_message(txt.stop)
	return END


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
			MAIN: [
				# begin_game_handler,
				# profile_handler,
				CallbackQueryHandler(
					common.pickMenuOption,
					pattern=r'^({})$'.format(')|('.join(reply_args.keys()))
				),
				admin_handler
			],
			HOW: [],
			ABOUT: [],
		},
		fallbacks=[
			CallbackQueryHandler(back, pattern=r'^back$'),
			CommandHandler('stop', stop),
			MessageHandler(Filters.all, again)
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
