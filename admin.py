from logging import getLogger

from telegram import ParseMode
from telegram.ext import (
	ConversationHandler, CommandHandler,
	MessageHandler, CallbackQueryHandler, Filters
)

import config as cnf
import markups as mrk
import texts as txt
import common

########################

logger = getLogger('admin')

END, MAIN, SPAM, ADMINS, SERVERS, API = range(-1, 5)


def adminMenu(update, context):
	update.callback_query.edit_message_text(
		txt.admin['message'],
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=mrk.admin_menu
	)
	context.user_data['conv_level'] = MAIN
	return MAIN


def back(update, context):
	if context.user_data['conv_level'] != MAIN:
		return adminMenu(update, context)
	update.callback_query.edit_message_text(
		txt.main['message'],
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=mrk.main_menu_admin
			if update.effective_user.id in cnf.admin_id
			else mrk.main_menu_user
	)
	return END


reply_args = {
	'spam'		: (SPAM, txt.admin['buttons']['spam']['message'], mrk.spam),
	'admins'	: (ADMINS, txt.admin['buttons']['admins']['message'], mrk.admins),
	'servers'	: (SERVERS, txt.admin['buttons']['servers']['message'], mrk.servers),
	'pubg_api'	: (API, txt.admin['buttons']['pubg_api']['message'], mrk.pubg_api),
}
common.reply_args = reply_args

admin_handler = ConversationHandler(
	entry_points=[
		CallbackQueryHandler(adminMenu, pattern=r'^admin$')
	],
	states={
		MAIN: [
			CallbackQueryHandler(
				common.pickMenuOption,
				pattern=r'^({})$'.format(')|('.join(reply_args.keys()))
			)
		],
		SPAM: [],
		ADMINS: [],
		SERVERS: [],
		API: [],
	},
	map_to_parent={
		END: MAIN,
	},
	fallbacks=[
		# CallbackQueryHandler(back, pattern=r'^back$')
	],
	conversation_timeout=1200
)
