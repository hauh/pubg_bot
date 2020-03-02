from logging import getLogger
import re

from telegram.ext import (
	ConversationHandler, CallbackQueryHandler,
	Filters, MessageHandler
)

import config
import texts
import menu
import database

#######################

logger = getLogger(__name__)
PROFILE, GET_VALUE, UPDATE = range(0, 3)
profile_menu = texts.menu['next']['profile']


def profileMain(update, context):
	if 'new_value' in context.user_data:
		del context.user_data['new_value']
	menu.sendMessage(
		update, context,
		profile_menu['msg'].format(
			update.effective_user.id,
			context.user_data['pubg_id'],
			context.user_data['balance'],
		),
		profile_menu['buttons'],
		'profile'
	)
	return PROFILE


def balanceHistory(update, context):
	current_menu = profile_menu['next']['balance_history']
	balance_history = database.getBalanceHistory(int(update.effective_user.id))
	if balance_history:
		message = ""
		for balance_entry in balance_history:
			amount = balance_entry['amount']
			message += "{arrow} \[{id}: {date}] {amount}\n".format(
				arrow='➡' if amount > 0 else '⬅',
				id=balance_entry['id'],
				date=balance_entry['date'],
				amount=amount
			)
	else:
		message = current_menu['msg']
	menu.sendMessage(
		update, context,
		message,
		profile_menu['next']['balance_history']['buttons'],
		'balance_history'
	)


def updateProfile(update, context):
	what_to_update = update.callback_query.data
	current_menu = profile_menu['next'][what_to_update]
	menu.sendMessage(
		update, context,
		current_menu['msg'],
		current_menu['buttons'][1:],
		what_to_update
	)
	return GET_VALUE


def getValue(update, context):
	new_value = int(update.effective_message.text)
	update.effective_message.delete()
	context.user_data['new_value'] = new_value
	what_to_update = context.user_data['conv_history'].pop()
	current_menu = profile_menu['next'][what_to_update]
	menu.sendMessage(
		update, context,
		current_menu['msg_with_value'].format(new_value),
		current_menu['buttons'],
		what_to_update
	)
	return UPDATE


def addFunds(user_id, user_data):
	database.updateBalance(user_id, user_data['new_value'])
	user_data['balance'] = database.getUser(user_id)['balance']
	return texts.funds_added


def withdrawFunds(user_id, user_data):
	amount = user_data['new_value']
	current_funds = database.getUser(user_id)['balance']
	if current_funds < amount:
		return texts.insufficient_funds
	database.updateBalance(user_id, -amount)
	user_data['balance'] = database.getUser(user_id)['balance']
	return texts.funds_withdrawn


def updatePubgID(user_id, user_data):
	new_id = user_data['new_value']
	# if not check_id(new_id):
	# 	return texts.pubg_id_not_found
	database.updatePubgID(user_id, new_id)
	user_data['pubg_id'] = new_id
	return texts.pubg_id_is_set


update_profile_callbacks = {
	'add_funds'		: addFunds,
	'withdraw_funds': withdrawFunds,
	'set_pubg_id'	: updatePubgID,
}


def doUpdate(update, context):
	what_to_update = context.user_data['conv_history'].pop()
	result = update_profile_callbacks[what_to_update](
		int(update.effective_user.id),
		context.user_data
	)
	update.callback_query.answer(result)
	del context.user_data['new_value']
	return profileMain(update, context)


handler = ConversationHandler(
	entry_points=[
		CallbackQueryHandler(profileMain, pattern=r'^profile$')
	],
	states={
		PROFILE: [
			CallbackQueryHandler(balanceHistory, pattern=r'^balance_history$'),
			CallbackQueryHandler(
				updateProfile,
				pattern=r'^({})$'.format(')|('.join(profile_menu['next'].keys()))),
		],
		GET_VALUE: [
			MessageHandler(Filters.regex(r'^[0-9]+$'), getValue),
		],
		UPDATE: [
			CallbackQueryHandler(doUpdate, pattern=r'^confirm$')
		]
	},
	fallbacks=[],
	allow_reentry=True
)
