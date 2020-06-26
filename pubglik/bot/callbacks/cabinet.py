"""User profile management"""

import re

from telegram import ChatAction
from psycopg2.errors import UniqueViolation

from pubglik import database
from pubglik.bot.misc import unitpay

##############################


def main(conversation, context):
	return conversation.reply(conversation.state.texts.format(
		user_id=conversation.user_id,
		pubg_id=context.user_data.get('pubg_username') or '-',
		pubg_username=context.user_data.get('pubg_id') or '-',
		balance=context.user_data.get('balance') or 0
	))


def balance_history(conversation, context):
	if not (history := database.get_balance_history(conversation.user_id)):
		return conversation.reply(conversation.state.texts['not_found'])
	return conversation.reply(
		"\n".join([conversation.state.texts['template'].format(
			arrow='➡' if balance_entry['amount'] > 0 else '⬅',
			id=balance_entry['id'],
			date=balance_entry['date'].strftime("%Y.%m.%d %H:%M"),
			amount=balance_entry['amount']
		) for balance_entry in history]),
	)


def with_input(setter):
	def handle_input(conversation, context):
		# if no input say what to do here
		if not conversation.input:
			return conversation.reply(conversation.state.texts['input'])

		# check input if it's not confirmed yet
		if not conversation.confirmed:
			if not setter(conversation, context, validate=True):
				return conversation.reply(conversation.state.texts['invalid'])

			conversation.add_button(
				conversation.state.confirm_button(conversation.input))
			return conversation.reply(
				conversation.state.texts['confirm'].format(conversation.input))

		return setter(conversation, context)
	return handle_input


@with_input
def set_pubg_username(conversation, context, validate=False):
	if validate:
		return len(conversation.input) < 15

	try:
		database.update_user(conversation.user_id, pubg_username=conversation.input)
	except UniqueViolation:
		conversation.set_answer(conversation.state.answers['duplicate'])
		return conversation.reply(conversation.state.texts['input'])

	context.user_data['pubg_username'] = conversation.input
	conversation.set_answer(conversation.state.answers['success'])
	return conversation.back(context)


@with_input
def set_pubg_id(conversation, context, validate=False):
	if validate:
		return re.match(r'^[1-9][0-9]{7,9}$', conversation.input)

	try:
		database.update_user(conversation.user_id, pubg_id=int(conversation.input))
	except UniqueViolation:
		conversation.set_answer(conversation.state.answers['duplicate'])
		return conversation.reply(conversation.state.texts['input'])

	context.user_data['pubg_id'] = int(conversation.input)
	conversation.set_answer(conversation.state.answers['success'])
	return conversation.back(context)


@with_input
def add_funds(conversation, context, validate=False):
	if validate:
		return re.match(r'^[1-9][0-9]{1,4}$', conversation.input)

	context.bot.send_chat_action(conversation.user_id, ChatAction.TYPING)
	button_url = unitpay.invoice_url(str(conversation.user_id), conversation.input)  # noqa
	conversation.add_button(
		conversation.state.extra['goto_payment'](conversation.input, button_url))
	return conversation.reply(conversation.state.texts['input'])


def withdraw_money(conversation, context):
	text = conversation.state.texts['money'].format(context.user_data['balance'])
	details = context.user_data.setdefault(
		'withdrawal_details', dict.fromkeys(['provider', 'account', 'amount']))
	for key, detail in details.items():
		if detail:
			# noqa todo: proper providers names
			text += conversation.state.texts[key].format(detail)

	# set all withdrawal details first
	if not all(details.values()):
		return conversation.reply(text)

	# checking commission
	context.bot.send_chat_action(conversation.user_id, ChatAction.TYPING)
	if (commission := unitpay.check_commission(details['provider'])) is None:
		conversation.set_answer(conversation.state.answers['error'])
		return conversation.back(context)

	total = round(details['amount'] * (1 + commission / 100))
	text += conversation.state.texts['commission'].format(commission, total)

	# confirm first
	if not conversation.confirmed:
		conversation.add_button(conversation.state.confirm_button(""))
		return conversation.reply(text)

	del context.user_data['withdrawal_details']['amount']

	# not enough money
	if (current_balance := database.get_balance(conversation.user_id)) < total:
		context.user_data['balance'] = current_balance
		conversation.set_answer(conversation.state.texts['too_much'])
		return conversation.reply(text)

	# finally processing money
	transaction = database.withdraw_money(conversation.user_id, total)  # generatr
	transaction_id = next(transaction)
	try:
		answer, payment_id = unitpay.make_payment(transaction_id, total, **details)
		conversation.set_answer({'text': answer, 'show_alert': True})
	except OSError as err:  # connection error or problems with account
		conversation.set_answer(conversation.state.answers['error'])
		payment_id = None
		context.bot.notify_admins(
			conversation.state.texts['payment_error'].format(
				conversation.user_id, context.user_data['pubg_username'], err.args[0]),
		)

	# if payment_id is None means payment failed means no new balance, reconfirm
	new_balance = transaction.send(payment_id)
	transaction.close()
	if not new_balance:
		return conversation.reply(text)

	# all good, returning back to profile
	context.user_data['balance'] = new_balance
	return conversation.back(context)


def set_withdrawal_provider(conversation, context):
	if not conversation.input:
		return conversation.reply(conversation.state.texts)

	context.user_data['withdrawal_details']['provider'] = conversation.input
	return conversation.back(context)


@with_input
def set_withdrawal_account(conversation, context, validate=False):
	details = context.user_data.get('withdrawal_details', {})
	if validate:
		if account_format := unitpay.providers.get(details.get('provider')):
			return re.match(account_format, conversation.input)
		return any(re.match(account_format, conversation.input)
					for account_format in unitpay.providers.values())

	details['account'] = conversation.input
	return conversation.back(context)


@with_input
def set_withdrawal_amount(conversation, context, validate=False):
	if validate:
		return re.match(r'^[1-9][0-9]{1,4}$', conversation.input)

	if (amount := int(conversation.input)) > context.user_data['balance']:
		conversation.set_answer(conversation.state.answers['too_much'])
		return conversation.reply(conversation.state.texts)

	context.user_data['withdrawal_details']['amount'] = amount
	return conversation.back(context)
