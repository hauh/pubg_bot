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
import buttons

#######################

logger = getLogger(__name__)
profile_menu = texts.menu['next']['profile']


def main(update, context, menu):
	return (
		profile_menu['msg'].format(
			user_id=update.effective_user.id,
			pubg_id=context.user_data['pubg_username'] or '-',
			pubg_username=context.user_data['pubg_id'] or '-',
			balance=context.user_data['balance'],
		),
		profile_menu['buttons'],
	)


def balanceHistory(update, context, menu):
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


def addFunds(user_id, user_data, amount):
	user_data['balance'] = database.updateBalance(user_id, int(amount))
	return True


def withdrawFunds(user_id, user_data, amount):
	current_funds = database.getUser(user_id)['balance']
	amount = int(amount)
	if current_funds < amount:
		return False
	user_data['balance'] = database.updateBalance(user_id, -amount)
	return True


def setPubgID(user_id, user_data, pubg_id):
	database.updatePubgID(user_id, int(pubg_id))
	user_data['pubg_id'] = pubg_id
	return True


def setPubgUsername(user_id, user_data, pubg_username):
	database.updatePubgUsername(user_id, pubg_username)
	user_data['pubg_username'] = pubg_username
	return True


update_profile_callbacks = {
	'add_funds'			: addFunds,
	'withdraw_funds'	: withdrawFunds,
	'set_pubg_id'		: setPubgID,
	'set_pubg_username'	: setPubgUsername
}


def updateProfile(update, context, menu):
	validated_input = context.chat_data.pop('validated_input', None)
	what_to_update = context.chat_data['history'][-1]
	current_menu = profile_menu['next'][what_to_update]

	if validated_input:
		if update_profile_callbacks[what_to_update](
			int(update.effective_user.id), context.user_data, validated_input):
			answer = current_menu['input']['msg_success']
		else:
			answer = current_menu['input']['msg_fail']
		update.callback_query.answer(answer, show_alert=True)
		context.chat_data['history'].pop()
		return main(update, context, menu)

	user_input = context.chat_data.pop('user_input', None)
	confirm_button = []
	if not user_input:
		message = current_menu['msg']
	elif (what_to_update.endswith('username') and len(user_input) <= 14)\
		or re.match(r'^[0-9]{5,10}$', user_input):
		message = current_menu['input']['msg_valid'].format(user_input)
		confirm_button = [buttons.createButton(
			texts.confirm, f'confirm_{user_input}')]
	else:
		message = current_menu['input']['msg_error']
	return (message, [confirm_button] + current_menu['buttons'])
