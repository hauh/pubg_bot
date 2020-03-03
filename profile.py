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
profile_menu = texts.menu['next']['profile']


def profileMain(update, context):
	if 'user_input' in context.user_data:
		del context.user_data['user_input']
	return (
		profile_menu['msg'].format(
			update.effective_user.id,
			context.user_data['pubg_id'],
			context.user_data['balance'],
		),
		profile_menu['buttons'],
	)


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
	return (
		message,
		profile_menu['next']['balance_history']['buttons'],
	)


def updateProfile(update, context):
	show_confirm = False
	if 'user_input' in context.chat_data:
		what_to_update = context.chat_data['history'].pop()
		if re.match(r'^[0-9]+$', context.chat_data['user_input']):
			show_confirm = True
		else:
			del context.chat_data['user_input']
	else:
		what_to_update = update.callback_query.data
	current_menu = profile_menu['next'][what_to_update]
	if show_confirm:
		message = current_menu['msg_with_value'].format(
			context.chat_data['user_input'])
		buttons = current_menu['buttons']
	else:
		message = current_menu['msg']
		buttons = current_menu['buttons'][1:]
	return (message, buttons)


def addFunds(user_id, user_data, new_value):
	database.updateBalance(user_id, new_value)
	user_data['balance'] = database.getUser(user_id)['balance']
	return texts.funds_added


def withdrawFunds(user_id, user_data, new_value):
	current_funds = database.getUser(user_id)['balance']
	if current_funds < new_value:
		return texts.insufficient_funds
	database.updateBalance(user_id, -new_value)
	user_data['balance'] -= new_value
	return texts.funds_withdrawn


def updatePubgID(user_id, user_data, new_value):
	# if not check_id(new_id):
	# 	return texts.pubg_id_not_found
	database.updatePubgID(user_id, new_value)
	user_data['pubg_id'] = new_value
	return texts.pubg_id_is_set


update_profile_callbacks = {
	'add_funds'		: addFunds,
	'withdraw_funds': withdrawFunds,
	'set_pubg_id'	: updatePubgID,
}


def doUpdate(update, context):
	what_to_update = context.chat_data['history'].pop()
	result = update_profile_callbacks[what_to_update](
		int(update.effective_user.id),
		context.user_data,
		int(context.chat_data['user_input'])
	)
	update.callback_query.answer(result, show_alert=True)
	del context.chat_data['user_input']
	return profileMain(update, context)


callbacks = {
	'profile'			: profileMain,
	'balance_history'	: balanceHistory,
	'add_funds'			: updateProfile,
	'withdraw_funds'	: updateProfile,
	'set_pubg_id'		: updateProfile,
	'profile_confirm'	: doUpdate,
}
