"""User profile management"""

import re

from telegram import ChatAction
from psycopg2.errors import UniqueViolation

from pubglik import database
from pubglik.bot.misc import unitpay

##############################


def main(state, conversation, context):
	return conversation.reply(state.texts.format(
		user_id=conversation.user_id,
		pubg_id=context.user_data.get('pubg_username') or '-',
		pubg_username=context.user_data.get('pubg_id') or '-',
		balance=context.user_data.get('balance') or 0
	))


def balance_history(state, conversation, context):
	if not (history := database.get_balance_history(conversation.user_id)):
		return conversation.reply(state.texts['not_found'])
	return conversation.reply(
		"\n".join([state.texts['template'].format(
			arrow='➡' if balance_entry['amount'] > 0 else '⬅',
			id=balance_entry['id'],
			date=balance_entry['date'].strftime("%Y.%m.%d %H:%M"),
			amount=balance_entry['amount']
		) for balance_entry in history]),
	)


def with_input(setter):
	def handle_input(state, conversation, context):
		# if no input say what to do here
		if not conversation.input:
			return conversation.reply(state.texts['input'])

		# check input if it's not confirmed yet
		if not conversation.confirmed:
			if not setter(state, conversation, context, validate=True):
				return conversation.reply(state.texts['invalid'])

			return conversation.reply(
				text=state.texts['confirm'].format(conversation.input),
				confirm=conversation.input
			)

		return setter(state, conversation, context)
	return handle_input


@with_input
def set_pubg_username(state, conversation, context, validate=False):
	if validate:
		return len(conversation.input) < 15

	try:
		database.update_user(conversation.user_id, pubg_username=conversation.input)
	except UniqueViolation:
		return conversation.reply(state.texts['input'], answer='duplicate')

	context.user_data['pubg_username'] = conversation.input
	return conversation.back(context, answer='success')


@with_input
def set_pubg_id(state, conversation, context, validate=False):
	if validate:
		return re.match(r'^[1-9][0-9]{7,9}$', conversation.input)

	try:
		database.update_user(conversation.user_id, pubg_id=int(conversation.input))
	except UniqueViolation:
		return conversation.reply(state.texts['input'], answer='duplicate')

	context.user_data['pubg_id'] = int(conversation.input)
	return conversation.back(context, answer='success')


@with_input
def add_funds(state, conversation, context, validate=False):
	if validate:
		return re.match(r'^[1-9][0-9]{1,4}$', conversation.input)

	conversation.update.effective_chat.send_action(ChatAction.TYPING)
	button_url = unitpay.invoice_url(str(conversation.user_id), conversation.input)  # noqa
	return conversation.reply(
		text=state.texts['input'],
		extra_buttons=(state.extra['goto_payment'](conversation.input, button_url),)
	)


def withdraw_money(state, conversation, context):
	details = context.user_data.setdefault(
		'withdrawal_details', dict.fromkeys(['provider', 'account', 'amount']))
	text = state.texts['money'].format(context.user_data['balance'])
	for key, detail in details.items():
		if detail:
			if key != 'provider':
				text += state.texts[key].format(detail)
			else:
				for button in state.next['provider'].buttons:
					if button[0].callback_data == f'provider;{detail}':
						text += state.texts['provider'].format(button[0].text)
						break

	# set all withdrawal details first
	if not all(details.values()):
		return conversation.reply(text)

	# checking commission
	if not (total := context.user_data.get('withdrawal_total')):
		conversation.update.effective_chat.send_action(ChatAction.TYPING)
		if (commission := unitpay.check_commission(details['provider'])) is None:
			return conversation.back(context, answer='error')

		total = round(details['amount'] * (1 + commission / 100))
		context.user_data['withdrawal_total'] = total

	if not conversation.confirmed:
		text += state.texts['commission'].format(total)
		return conversation.reply(text, confirm='withdraw')

	del context.user_data['withdrawal_total']

	# not enough money
	if (current_balance := database.get_balance(conversation.user_id)) < total:
		context.user_data['balance'] = current_balance
		details['amount'] = None
		return conversation.reply(text, answer='too_much')

	conversation.update.effective_chat.send_action(ChatAction.TYPING)
	# finally processing money
	transaction = database.withdraw_money(conversation.user_id, total)  # generat.
	transaction_id = next(transaction)
	try:
		answer, payment_id = unitpay.make_payment(transaction_id, **details)

	except OSError as err:  # connection error or problems with our account
		transaction.send(None)
		context.bot.notify_admins(
			state.texts['payment_error'].format(
				context.user_data['username'],
				context.user_data['pubg_username'],
				err.args[0]
			)
		)
		return conversation.back(context, answer='error')

	except ValueError as err:  # error caused by user
		transaction.send(None)
		return conversation.reply(text, answer=err.args[0])

	else:
		context.user_data['balance'] = transaction.send(payment_id)
		del context.user_data['withdrawal_details']
		return conversation.back(context, answer=answer)

	finally:
		transaction.close()


def set_withdrawal_provider(state, conversation, context):
	if not conversation.input:
		return conversation.reply()

	context.user_data['withdrawal_details']['provider'] = conversation.input
	return conversation.back(context)


@with_input
def set_withdrawal_account(state, conversation, context, validate=False):
	details = context.user_data.get('withdrawal_details', {})
	if validate:
		if provider := details.get('provider'):
			return re.match(unitpay.providers.get(provider), conversation.input)
		return any(re.match(account_format, conversation.input)
				for account_format in unitpay.providers.values())

	details['account'] = conversation.input
	return conversation.back(context)


@with_input
def set_withdrawal_amount(state, conversation, context, validate=False):
	if validate:
		return re.match(r'^[1-9][0-9]{1,4}$', conversation.input)

	if (amount := int(conversation.input)) > context.user_data['balance']:
		return conversation.reply(answer='too_much')

	context.user_data['withdrawal_details']['amount'] = amount
	context.user_data.pop('withdrawal_total', None)
	return conversation.back(context)
