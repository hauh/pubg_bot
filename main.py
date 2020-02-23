from logging import getLogger

from telegram import ParseMode
from telegram.ext import (
	Updater, ConversationHandler, CommandHandler,
	MessageHandler, CallbackQueryHandler, Filters
)

import config as cnf
import markups as mrk
import texts as txt
import menu_template as menu
from admin import admin_handler

########################

logger = getLogger('bot')

END = -1
MAIN = 0


def start(update, context):
	update.effective_chat.send_message(
		txt.main['msg'],
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=mrk.main_menu_admin
			if update.effective_user.id in cnf.admin_id
			else mrk.main_menu_user
	)
	context.user_data['main_level'] = MAIN
	return MAIN


main_menu = {
	'main': {
		'message'	: txt.main['msg'],
		'keyboard'	: mrk.main_menu_admin,
	},
	'matches': {
		'message'	: txt.matches['msg'],
		'keyboard'	: mrk.main_menu_admin,
		'back'		: 'main'
	},
	'room': {
		'message'	: txt.main['next']['room']['msg'],
		'keyboard'	: mrk.main_menu_admin,
		'back'		: 'main'
	},
	'profile': {
		'message'	: txt.profile['msg'],
		'keyboard'	: mrk.main_menu_admin,
		'back'		: 'main'
	},
	'how': {
		'message'	: txt.main['next']['how']['msg'],
		'keyboard'	: mrk.how,
		'back'		: 'main'
	},
	'points': {
		'message'	: txt.main['next']['how']['next']['points']['msg'],
		'keyboard'	: mrk.how,
		'back'		: 'how'
	},
	'service': {
		'message'	: txt.main['next']['how']['next']['service']['msg'],
		'keyboard'	: mrk.how,
		'back'		: 'how'
	},
	'faq': {
		'message'	: txt.main['next']['how']['next']['faq']['msg'],
		'keyboard'	: mrk.how,
		'back'		: 'how'
	},
	'about': {
		'message'	: txt.main['next']['about']['msg'],
		'keyboard'	: mrk.about,
		'back'		: 'main'
	}
}


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

	main_handler = menu.createConversationHandler(main_menu['main'], main_menu)
	main_handler.entry_points = [CommandHandler('start', start)]
	main_handler.states['main'].append(admin_handler)

	dispatcher.add_handler(main_handler)
	dispatcher.add_error_handler(error)

	logger.info('Bot started')

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
