from logging import getLogger

from telegram import ParseMode
from telegram.ext import (
	CommandHandler, MessageHandler,
	CallbackQueryHandler, Filters
)

import config as cnf
import markups as mrk
import texts as txt
import menu_template as menu

########################

logger = getLogger('admin')

main_menu = {
	'main'		: txt.main['msg'],
	'keyboard'	: mrk.main_menu_admin,
}
menus = {
	'admin': {
		'message'	: txt.admin['msg'],
		'keyboard'	: mrk.admin_menu,
	},
	'spam': {
		'message'	: txt.admin['next']['spam']['msg'],
		'keyboard'	: mrk.spam,
		'back'		: 'admin'
	},
	'admins': {
		'message'	: txt.admin['next']['admins']['msg'],
		'keyboard'	: mrk.admins,
		'back'		: 'admin'
	},
	'servers': {
		'message'	: txt.admin['next']['servers']['msg'],
		'keyboard'	: mrk.servers,
		'back'		: 'admin'
	},
	'pubg_api': {
		'message'	: txt.admin['next']['pubg_api']['next'],
		'keyboard'	: mrk.pubg_api,
		'back'		: 'admin'
	}
}

admin_handler = menu.createConversationHandler(main_menu, menus)
