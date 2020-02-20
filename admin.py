from logging import getLogger

from telegram import ParseMode
from telegram.ext import (
	ConversationHandler, CommandHandler,
	MessageHandler, CallbackQueryHandler, Filters
)

import config as cnf
import messages as msg
import markups as mrk

########################

logger = getLogger('admin')

MAIN, SPAM, ADMINS, SERVERS, API = range(1, 6)


def adminMenu(update, context):
	update.effective_chat.send_message(
		msg.admin,
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=mrk.admin_menu
	)
	context.user_data['adm_conv_level'] = MAIN
	return MAIN


def spam(update, context):
	update.effective_chat.send_message(
		msg.spam,
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=mrk.back
	)
	context.user_data['adm_conv_level'] = SPAM
	return SPAM


def manageAdmins(update, context):
	update.effective_chat.send_message(
		msg.manage_admins,
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=mrk.back
	)
	context.user_data['adm_conv_level'] = ADMINS
	return ADMINS


def manageServers(update, context):
	update.effective_chat.send_message(
		msg.manage_servers,
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=mrk.back
	)
	context.user_data['adm_conv_level'] = SERVERS
	return SERVERS


def manageAPI(update, context):
	update.effective_chat.send_message(
		msg.manage_pubg_api,
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=mrk.back
	)
	context.user_data['adm_conv_level'] = API
	return API


def back(update, context):
	if context.user_data['adm_conv_level'] != MAIN:
		return adminMenu(update, context)
	update.effective_chat.send_message(
		msg.start,
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=mrk.start_admin
			if update.effective_user.id in cnf.admin_id
			else mrk.start_user
	)
	del context.user_data['adm_conv_level']
	return ConversationHandler.END


admin_handler = ConversationHandler(
	entry_points=[
		CallbackQueryHandler(adminMenu, pattern=r'^admin$')
	],
	states={
		MAIN: [
			CallbackQueryHandler(spam, pattern=r'^spam$'),
			CallbackQueryHandler(manageAdmins, pattern=r'^manage_admins$'),
			CallbackQueryHandler(manageServers, pattern=r'^manage_servers$'),
			CallbackQueryHandler(manageAPI, pattern=r'^manage_pubg_api$'),
		],
		SPAM: [],
		ADMINS: [],
		SERVERS: [],
		API: [],
	},
	map_to_parent={
		ConversationHandler.END: 'MAIN',
	},
	fallbacks=[
		CallbackQueryHandler(back, pattern=r'^back$')
	],
	conversation_timeout=1200
)
