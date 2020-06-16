"""User profile management"""

import re

from telegram import ChatAction
from psycopg2.errors import UniqueViolation

import texts
import database
import unitpay
import utility

##############################

profile_menu = texts.menu['next']['profile']
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
				context.user_data['conversation'].back()
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
		return re.match(r'^[1-9][0-9]{7,9}$', user_input)

	pubg_id = int(user_input)
	try:
		database.update_user(update.effective_user.id, pubg_id=pubg_id)
	except UniqueViolation:
		return 'duplicate', None

	context.user_data['pubg_id'] = pubg_id
	return 'success', profile_main


@with_input
def add_funds(update, context, user_input, validated):
	if not validated:
		return re.match(r'^[1-9][0-9]{1,4}$', user_input)

	btn = utility.button(None, texts.goto_payment.format(user_input))
	btn[0].url = unitpay.invoice_url(str(update.effective_user.id), user_input)
	menu = profile_menu['next']['add_funds']
	return None, lambda *_: (menu['msg'], [btn] + menu['buttons'])


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
	if (commission := unitpay.check_commission(details['provider'])) is None:
		update.callback_query.answer(menu['answers']['error'], show_alert=True)
		return (message, menu['buttons'])

	total = round(details['amount'] * (1 + commission / 100))

	# confirm first
	if not context.user_data.pop('validated_input', None):
		return (
			message + menu['answers']['commission'].format(commission, total),
			[utility.confirm_button('withdraw')] + menu['buttons']
		)

	user_id = update.effective_user.id
	del context.user_data['withdraw_details']['amount']

	# not enough money
	if (current_balance := database.get_balance(user_id)) < total:
		context.user_data['balance'] = current_balance
		update.callback_query.answer(menu['answers']['too_much'], show_alert=True)
		return (message, menu['buttons'])

	# finally processing money
	transaction = database.withdraw_money(user_id, total)  # generator
	transaction_id = next(transaction)
	try:
		answer, payment_id = unitpay.make_payment(transaction_id, total, **details)
	except OSError as err:  # connection error or problems with account
		answer, payment_id = menu['answers']['error'], None
		utility.notify_admins(
			texts.payment_error.format(
				user_id, context.user_data['pubg_username'], err.args[0]),
			context
		)
	try:
		# if payment_id is None means payment failed means no new balance, reconfirm
		if not (new_balance := transaction.send(payment_id)):
			return (
				message + menu['answers']['commission'].format(commission, total),
				[utility.confirm_button('withdraw')] + menu['buttons']
			)

		# all good, returning back to profile
		context.user_data['balance'] = new_balance
		context.user_data['conversation'].back()
		return profile_main(update, context)

	finally:
		transaction.close()
		update.callback_query.answer(answer, show_alert=True)


def get_withdraw_provider(update, context, menu):
	context.user_data['withdraw_details']['provider'] = update.callback_query.data
	context.user_data['conversation'].back(level=2)
	return withdraw_money(update, context)


@with_input
def get_withdraw_account(update, context, user_input, validated):
	details = context.user_data.get('withdraw_details', {})
	if not validated:
		if account_format := unitpay.providers.get(details.get('provider')):
			return re.match(account_format, user_input)
		return any(re.match(account_format, user_input)
					for account_format in unitpay.providers.values())

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
	profile_menu['next']['add_funds']['callback'] = add_funds

	withdraw_money_menu['callback'] = withdraw_money
	for provider in withdraw_money_menu['next']['provider']['next'].values():
		provider['callback'] = get_withdraw_provider
	withdraw_money_menu['next']['account']['callback'] = get_withdraw_account
	withdraw_money_menu['next']['amount']['callback'] = get_withdraw_amount
