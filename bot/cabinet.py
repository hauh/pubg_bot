'''User profile management'''

import re
import random

from telegram import ChatAction
from psycopg2.errors import UniqueViolation

import texts
import database
import qiwi
import utility

##############################

profile_menu = texts.menu['next']['profile']
add_funds_menu = profile_menu['next']['add_funds']
withdraw_money_menu = profile_menu['next']['withdraw_money']


def profile_main(update, context, menu=profile_menu):
	return (
		menu['msg'].format(
			user_id=update.effective_user.id,
			pubg_id=context.user_data['pubg_username'] or '-',
			pubg_username=context.user_data['pubg_id'] or '-',
			balance=context.user_data['balance'],
		),
		menu['buttons']
	)


def balance_history(update, context, menu):
	if not (history := database.get_balance_history(update.effective_user.id)):
		return (menu['msg'], menu['buttons'])
	return (
		"\n".join(["{arrow} \\[{id}: {date}] *{amount}*".format(
			arrow='➡' if balance_entry['amount'] > 0 else '⬅',
			id=balance_entry['id'],
			date=balance_entry['date'].strftime("%Y.%m.%d %H:%M"),
			amount=balance_entry['amount']
		) for balance_entry in history]),
		menu['buttons']
	)


def with_input(setter):
	def handle_input(update, context, menu):
		# if input validated and confirmed set and return back
		if validated_input := context.user_data.pop('validated_input', None):
			answer, back = setter(update, context, validated_input, validated=True)
			if answer:
				update.callback_query.answer(
					menu['answers'][answer], show_alert=True)
			if back:
				del context.user_data['history'][-1]
				return back(update, context)

		# if no input say what to do here
		if not (user_input := context.user_data.pop('user_input', None)):
			return (menu['msg'], menu['buttons'])

		# validate first if there is input
		if not setter(update, context, user_input, validated=False):
			return (menu['answers']['invalid'], menu['buttons'])

		return (
			menu['answers']['confirm'].format(user_input),
			[utility.confirm_button(user_input)] + menu['buttons']
		)
	return handle_input


@with_input
def set_pubg_username(update, context, user_input, validated):
	if not validated:
		return len(user_input) <= 14

	try:
		database.update_user(update.effective_user.id, pubg_username=user_input)
	except UniqueViolation:
		return 'duplicate', None

	context.user_data['pubg_username'] = user_input
	return 'success', profile_main


@with_input
def set_pubg_id(update, context, user_input, validated):
	if not validated:
		return re.match(r'^[0-9]{8,10}$', user_input)

	pubg_id = int(user_input)
	try:
		database.update_user(update.effective_user.id, pubg_id=pubg_id)
	except UniqueViolation:
		return 'duplicate', None

	context.user_data['pubg_id'] = pubg_id
	return 'success', profile_main


def add_funds(update, context, menu=add_funds_menu):
	payment_code = context.user_data.setdefault(
		'payment_code', str(random.randint(100000, 999999)))
	return (menu['msg'].format(payment_code), menu['buttons'])


def check_income(update, context, menu):
	update.effective_chat.send_action(ChatAction.TYPING)
	if not (payment := qiwi.find_income(context.user_data['payment_code'])):
		update.callback_query.answer(menu['answers']['nothing'], show_alert=True)
		del context.user_data['history'][-1]
		return add_funds(update, context)

	amount, qiwi_id = payment
	context.user_data['balance'] = database.change_balance(
		update.effective_user.id, amount, 'income_qiwi', ext_id=qiwi_id)
	update.callback_query.answer(
		menu['answers']['success'].format(amount), show_alert=True)
	del context.user_data['payment_code']
	del context.user_data['history'][-2:]
	return profile_main(update, context)


def withdraw_money(update, context, menu=withdraw_money_menu):
	update.effective_chat.send_action(ChatAction.TYPING)
	details = context.user_data.setdefault(
		'withdraw_details', dict.fromkeys(['provider', 'account', 'amount']))
	message = menu['msg'].format(
		balance=context.user_data['balance'],
		**{key: value or menu['default'] for key, value in details.items()}
	)
	# set all withdraw details first
	if not all(details.values()):
		return (message, menu['buttons'])

	# checking commission
	if (commission := qiwi.check_commission(**details)) is None:
		update.callback_query.answer(menu['answers']['error'], show_alert=True)
		return (message, menu['buttons'])

	total = details['amount'] + commission

	# confirm first
	if not context.user_data.pop('validated_input', None):
		return (
			message + menu['answers']['commission'].format(commission, total),
			[utility.confirm_button('withdraw')] + menu['buttons']
		)

	user_id = update.effective_user.id

	# not enough money
	if (current_balance := database.get_balance(user_id)) < total:
		context.user_data['balance'] = current_balance
		del context.user_data['withdraw_details']['amount']
		update.callback_query.answer(menu['answers']['too_much'], show_alert=True)
		return (message, menu['buttons'])

	# money withdrawn
	if (new_balance := database.withdraw_money(user_id, **details)) is not None:
		context.user_data['balance'] = new_balance
		update.callback_query.answer(menu['answers']['success'], show_alert=True)

	# withdraw failed
	else:
		utility.notify_admins(texts.qiwi_error, context)
		update.callback_query.answer(menu['answers']['error'], show_alert=True)

	del context.user_data['withdraw_details']['amount']
	del context.user_data['history'][-1]
	return profile_main(update, context)


def get_withdraw_provider(update, context, menu):
	history = context.user_data.get('history')
	context.user_data['withdraw_details']['provider'] = history[-1]
	del history[-2:]
	return withdraw_money(update, context)


@with_input
def get_withdraw_account(update, context, user_input, validated):
	details = context.user_data.get('withdraw_details', {})
	if not validated:
		match_qiwi = re.match(r'^7[0-9]{10}$', user_input)
		match_card = re.match(r'^[0-9]{16}$', user_input)
		if (provider := details.get('provider')) is not None:
			if provider == 'qiwi':
				return match_qiwi
			return match_card
		return match_qiwi or match_card

	details['account'] = user_input
	return None, withdraw_money


@with_input
def get_withdraw_amount(update, context, user_input, validated):
	if not validated:
		return re.match(r'^[1-9][0-9]{1,4}$', user_input)

	if (amount := int(user_input)) > context.user_data['balance']:
		return 'too_much', None

	context.user_data['withdraw_details']['amount'] = amount
	return None, withdraw_money


##############################

def add_callbacks():
	profile_menu['callback'] = profile_main
	profile_menu['next']['set_pubg_id']['callback'] = set_pubg_id
	profile_menu['next']['set_pubg_username']['callback'] = set_pubg_username
	profile_menu['next']['balance_history']['callback'] = balance_history

	add_funds_menu['callback'] = add_funds
	add_funds_menu['next']['check_income']['callback'] = check_income

	withdraw_money_menu['callback'] = withdraw_money
	for provider in withdraw_money_menu['next']['provider']['next'].values():
		provider['callback'] = get_withdraw_provider
	withdraw_money_menu['next']['account']['callback'] = get_withdraw_account
	withdraw_money_menu['next']['amount']['callback'] = get_withdraw_amount
