import re
from logging import getLogger

from telegram import InlineKeyboardButton

import texts
import database

#######################

logger = getLogger(__name__)
profile_menu = texts.menu['next']['profile']


def mainProfile(update, context, menu=profile_menu):
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
	if balance_history:
		message = ""
		for balance_entry in balance_history:
			amount = balance_entry['amount']
			message += "{arrow} \[{id}: {date}] {amount}\n".format(
				arrow='➡' if amount > 0 else '⬅',
				id=balance_entry['id'],
				date=balance_entry['date'].strftime("%Y.%m.%d %H:%M"),
				amount=amount
			)
	else:
		message = menu['msg']
	return (message, menu['buttons'])


def withInput(setter_func):
	def checkInput(update, context, menu):
		validated_input = context.user_data.pop('validated_input', None)
		if validated_input:
			if setter_func(update, context, menu, validated_input, validated=True):
				update.callback_query.answer(menu['input']['msg_success'], show_alert=True)
			else:
				update.callback_query.answer(menu['input']['msg_fail'], show_alert=True)
			context.user_data['history'].pop()
			return mainProfile(update, context)

		user_input = context.user_data.pop('user_input', None)
		if not user_input:
			return (menu['msg'], menu['buttons'])

		if not setter_func(update, context, menu, user_input, validated=False):
			return (menu['input']['msg_error'], menu['buttons'])

		confirm_button = [InlineKeyboardButton(
			texts.confirm, callback_data=f'confirm_{user_input}')]
		return (
			menu['input']['msg_valid'].format(user_input),
			[confirm_button] + menu['buttons']
		)
	return checkInput


@withInput
def setPubgUsername(update, context, menu, user_input, validated):
	if not validated:
		return len(user_input) <= 14

	database.updatePubgUsername(int(update.effective_user.id), user_input)
	context.user_data['pubg_username'] = user_input
	return True


@withInput
def setPubgID(update, context, menu, user_input, validated):
	if not validated:
		return re.match(r'^[0-9]{8,10}$', user_input)

	pubg_id = int(user_input)
	database.updatePubgID(int(update.effective_user.id), pubg_id)
	context.user_data['pubg_id'] = pubg_id
	return True


@withInput
def addFunds(update, context, menu, user_input, validated):
	if not validated:
		return re.match(r'^[0-9]{2,5}$', user_input)

	context.user_data['balance'] = database.updateBalance(
		int(update.effective_user.id), int(user_input))
	return True


@withInput
def withdrawFunds(update, context, menu, user_input, validated):
	if not validated:
		return re.match(r'^[0-9]{3,5}$', user_input)

	user_id = int(update.effective_user.id)
	amount = int(user_input)
	current_funds = database.getUser(user_id)['balance']
	if current_funds < amount:
		return False
	context.user_data['balance'] = database.updateBalance(user_id, -amount)
	return True
