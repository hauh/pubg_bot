import re
from logging import getLogger

from telegram import InlineKeyboardButton

import texts
import database

#######################

logger = getLogger(__name__)


def mainProfile(update, context, menu):
	return (
		menu['msg'].format(
			user_id=update.effective_user.id,
			pubg_id=context.user_data['pubg_username'] or '-',
			pubg_username=context.user_data['pubg_id'] or '-',
			balance=context.user_data['balance'],
		),
		menu['buttons'],
	)


def balanceHistory(update, context, menu):
	balance_history = database.getBalanceHistory(int(update.effective_user.id))
	print("!!!")
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
		message = menu['msg']
	return (message, menu['buttons'])


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


def withInput(validation_func):
	def checkInput(update, context, menu):
		validated_input = context.user_data.pop('validated_input', None)
		if validated_input:
			what_to_update = context.user_data['history'].pop()
			if update_profile_callbacks[what_to_update](
				int(update.effective_user.id), context.user_data, validated_input):
				answer = menu['input']['msg_success']
			else:
				answer = menu['input']['msg_fail']
			update.callback_query.answer(answer, show_alert=True)
			return mainProfile(update, context, texts.menu['next']['profile'])

		user_input = context.user_data.pop('user_input', None)
		if not user_input:
			return (menu['msg'], menu['button'])

		if not validation_func(user_input):
			return (menu['input']['msg_error'], menu['buttons'])

		confirm_button = [InlineKeyboardButton(
			texts.confirm, callback_data=f'confirm_{user_input}')]
		return (menu['input']['msg_valid'], [confirm_button] + menu['buttons'])
	return checkInput


def setPubgUsername(user_input):
	return len(user_input) > 14


def setPubgID(user_input):
	return re.match(r'^[0-9]{8,10}$', user_input)


def moveFunds(user_input):
	return re.match(r'^[0-9]{3,5}$', user_input)
