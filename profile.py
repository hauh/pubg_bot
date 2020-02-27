from logging import getLogger
import re

from telegram.ext import (
	ConversationHandler, CallbackQueryHandler,
	Filters, MessageHandler
)

import config
import texts
import menu

#######################

logger = getLogger(__name__)
PROFILE = 0
SET_ID = 1


def profileMain(update, context):
	menu.sendMessage(
		update, context, 'profile',
		texts.profile['msg'].format(
			context.user_data['pubg_id'] if 'pubg_id' in context.user_data else '-'),
		texts.profile['buttons']
	)
	return PROFILE


def setPubgID(update, context):
	current_menu = texts.profile['next']['set_pubg_id']
	menu.sendMessage(
		update, context, 'set_pubg_id',
		current_menu['msg'],
		current_menu['buttons']
	)
	return SET_ID


def getPubgID(update, context):
	if not re.match(r'[0-9]+', update.effective_message.text):
		return setPubgID(update, context)
	context.user_data['pubg_id'] = update.effective_message.text
	return profileMain(update, context)


def addFunds(update, context):
	pass


def withdrawFunds(update, context):
	pass


handler = ConversationHandler(
	entry_points=[
		CallbackQueryHandler(profileMain, pattern=r'^profile$')
	],
	states={
		PROFILE: [
			CallbackQueryHandler(setPubgID, pattern=r'^set_pubg_id$'),
			CallbackQueryHandler(addFunds, pattern=r'^add_funds$'),
			CallbackQueryHandler(withdrawFunds, pattern=r'^withdraw_funds$'),
		],
		SET_ID: [
			MessageHandler(Filters.text, getPubgID)
		],
	},
	fallbacks=[],
	allow_reentry=True
)
