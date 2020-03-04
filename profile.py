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
	return (message, current_menu['buttons'])


def updateProfile(update, context):
	user_input = context.chat_data.pop('user_input', None)
	if user_input:
		return doUpdate(update, context, user_input)

	what_to_update = context.chat_data['history'][-1]
	current_menu = profile_menu['next'][what_to_update]
	if not update.callback_query and update.effective_message.text:
		return validateAndConfirm(update, context, current_menu)
	return (current_menu['msg'], current_menu['buttons'][1:])


def validateAndConfirm(update, context, current_menu):
	user_input = update.effective_message.text
	if re.match(r'^[0-9]+$', user_input):
		context.chat_data['user_input'] = user_input
		message = current_menu['input']['msg_valid'].format(user_input)
		buttons = current_menu['buttons']
	else:
		message = current_menu['input']['msg_error']
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


def doUpdate(update, context, validated_input):
	what_to_update = context.chat_data['history'].pop()
	result = update_profile_callbacks[what_to_update](
		int(update.effective_user.id),
		context.user_data,
		int(validated_input)
	)
	update.callback_query.answer(result, show_alert=True)
	return profileMain(update, context)


callbacks = {
	r'^profile$'									: profileMain,
	r'^balance_history$'							: balanceHistory,
	r'^(add_funds)|(withdraw_funds)|(set_pubg_id)$'	: updateProfile,
}
