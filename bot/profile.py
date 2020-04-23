import re
import random
from logging import getLogger

from telegram import ChatAction

import config
import texts
import database
import qiwi
import utility

##############################

logger = getLogger(__name__)
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
	if history := database.get_balance_history(update.effective_user.id):
		message = ""
		for balance_entry in history:
			amount = balance_entry['amount']
			message += "{arrow} \[{id}: {date}] *{amount}*\n".format(
				arrow='➡' if amount > 0 else '⬅',
				id=balance_entry['id'],
				date=balance_entry['date'].strftime("%Y.%m.%d %H:%M"),
				amount=amount
			)
	else:
		message = menu['msg']
	return (message, menu['buttons'])


def with_input(setter_func):
	def check_input(update, context, menu):
		if validated_input := context.user_data.pop('validated_input', None):
			if setter_func(update, context, menu, validated_input, validated=True):
				if 'msg_success' in menu['input']:
					update.callback_query.answer(
						menu['input']['msg_success'], show_alert=True)
			elif 'msg_fail' in menu['input']:
				update.callback_query.answer(
					menu['input']['msg_fail'], show_alert=True)
			context.user_data['history'].pop()
			prev = context.user_data['history'][-1]
			prev_menu = profile_menu['next'][prev]\
				if prev in profile_menu['next'] else profile_menu
			return prev_menu['callback'](update, context)

		if not (user_input := context.user_data.pop('user_input', None)):
			return (menu['msg'], menu['buttons'])

		if not setter_func(update, context, menu, user_input, validated=False):
			return (menu['input']['msg_error'], menu['buttons'])

		return (
			menu['input']['msg_valid'].format(user_input),
			[utility.confirmButton(user_input)] + menu['buttons']
		)
	return check_input


@with_input
def set_pubg_username(update, context, menu, user_input, validated):
	if not validated:
		return len(user_input) <= 14

	if not database.update_user(update.effective_user.id, pubg_username=user_input):
		return False
	context.user_data['pubg_username'] = user_input
	return True


@with_input
def set_pubg_id(update, context, menu, user_input, validated):
	if not validated:
		return re.match(r'^[0-9]{8,10}$', user_input)

	pubg_id = int(user_input)
	if not database.update_user(update.effective_user.id, pubg_id=pubg_id):
		return False
	context.user_data['pubg_id'] = pubg_id
	return True


def add_funds(update, context, menu=add_funds_menu):
	payment_code = context.user_data.setdefault(
		'payment_code', str(random.randint(100000, 999999)))
	return (
		menu['msg'].format(
			qiwi_phone=config.qiwi_phone,
			payment_code=payment_code
		),
		menu['buttons']
	)


def check_payment(update, context, menu):
	update.effective_chat.send_action(ChatAction.TYPING)
	if payment := qiwi.check_history(context.user_data['payment_code']):
		amount, qiwi_id = payment
		context.user_data['balance'] = database.change_balance(
			update.effective_user.id, amount,
			'income_qiwi', external_id=qiwi_id
		)
		answer_msg = menu['input']['msg_success'].format(amount)
		del context.user_data['payment_code']
	else:
		answer_msg = menu['input']['msg_error']
	update.callback_query.answer(answer_msg, show_alert=True)
	del context.user_data['history'][-2:]
	return add_funds(update, context)


def withdraw_money(update, context, menu=withdraw_money_menu):
	update.effective_chat.send_action(ChatAction.TYPING)
	details = context.user_data.setdefault(
		'withdraw_details', dict.fromkeys(['provider', 'account', 'amount']))
	confirm_button, commission_warning = [], ""
	if all(details.values()):
		if context.user_data.pop('validated_input', None) == 'withdraw':
			doWithdraw(update, context, menu, details)
		elif not (commission := qiwi.check_commission(**details)):
			callback_query.answer(menu['input']['msg_fail'], show_alert=True)
		else:
			confirm_button = utility.confirmButton('withdraw')
			commission_warning = menu['input']['msg_valid'].format(
				commission, details['amount'] + commission)
	return (
		menu['msg'].format(
			balance=context.user_data['balance'],
			**{key: value or menu['default'] for key, value in details.items()}
		) + commission_warning,
		[confirm_button] + menu['buttons']
	)


def get_withdraw_provider(update, context, menu):
	if details := context.user_data.get('withdraw_details'):
		details['provider'] = update.callback_query.data
	del context.user_data['history'][-2:]
	return withdraw_money(update, context)


@with_input
def get_withdraw_account(update, context, menu, user_input, validated):
	details = context.user_data.get('withdraw_details', {})
	if not validated:
		match_qiwi = re.match(r'^7[0-9]{10}$', user_input)
		match_card = re.match(r'^[0-9]{16}$', user_input)
		provider = details.get('provider')
		if provider is not None:
			if provider == 'qiwi':
				return match_qiwi
			return match_card
		return match_qiwi or match_card

	if not details:
		return False
	details['account'] = user_input
	return True


@with_input
def get_withdraw_amount(update, context, menu, user_input, validated):
	if not validated:
		return re.match(r'^[1-9][0-9]{1,4}$', user_input)

	if not (details := context.user_data.get('withdraw_details')):
		return False
	if (amount := int(user_input)) > context.user_data['balance']:
		return False

	details['amount'] = amount
	return True


def doWithdraw(update, context, menu, details):
	user_id = int(update.effective_user.id)
	answer_msg = None
	if commission := qiwi.check_commission(**details):
		amount = details['amount'] + commission
		context.user_data['balance'] = database.get_user(user_id)['balance']
		if context.user_data['balance'] < amount:
			answer_msg = menu['input']['msg_fail']
		elif (new_balance := database.withdraw_money(user_id, **details)) is not None:
			answer_msg = menu['input']['msg_success']
			context.user_data['balance'] = new_balance
		else:
			answer_msg = menu['input']['msg_error']
			context.bot.send_message(
				config.admin_group_id, texts.qiwi_error,
				reply_markup=InlineKeyboardMarkup(
					[[InlineKeyboardButton(texts.goto_qiwi, url=config.qiwi_url)]])
			)
	del context.user_data['withdraw_details']
	update.callback_query.answer(
		answer_msg or menu['input']['msg_fail'], show_alert=True)


##############################

profile_menu['callback'] = profile_main
profile_menu['next']['set_pubg_id']['callback'] = set_pubg_id
profile_menu['next']['set_pubg_username']['callback'] = set_pubg_username
profile_menu['next']['balance_history']['callback'] = balance_history

add_funds_menu['callback'] = add_funds
add_funds_menu['next']['next']['check_payment']['callback'] = check_payment

withdraw_money_menu['callback'] = withdraw_money
for provider in withdraw_money_menu['next']['provider']['next'].values():
	provider['callback'] = get_withdraw_provider
withdraw_money_menu['next']['account']['callback'] = get_withdraw_account
withdraw_money_menu['next']['amount']['callback'] = get_withdraw_amount
