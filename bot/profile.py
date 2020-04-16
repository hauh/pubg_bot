import re
import random
from logging import getLogger

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ChatAction

import config
import texts
import database
import qiwi

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
				if 'msg_success' in menu['input']:
					update.callback_query.answer(menu['input']['msg_success'], show_alert=True)
			elif 'msg_fail' in menu['input']:
				update.callback_query.answer(menu['input']['msg_fail'], show_alert=True)
			context.user_data['history'].pop()
			prev = context.user_data['history'][-1]
			prev_menu = profile_menu['next'][prev] if prev in profile_menu['next'] else profile_menu
			return prev_menu['callback'](update, context)

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


def addFunds(update, context, menu):
	payment_code = context.user_data.setdefault(
		'payment_code', str(random.randint(100000, 999999)))
	return (
		menu['msg'].format(
			qiwi_phone=config.qiwi_phone,
			payment_code=payment_code
		),
		menu['buttons']
	)


def checkPayment(update, context, menu):
	update.effective_chat.send_action(ChatAction.TYPING)
	if payment := qiwi.check_history(context.user_data['payment_code']):
		context.user_data['balance'] = database.updateBalance(
			int(update.effective_user.id), *payment)
		answer_msg = menu['input']['msg_success'].format(payment[1])
		del context.user_data['payment_code']
	else:
		answer_msg = menu['input']['msg_error']
	update.callback_query.answer(answer_msg, show_alert=True)
	del context.user_data['history'][-2]
	return mainProfile(update, context)


def doWithdraw(update, context, menu, details):
	user_id = int(update.effective_user.id)
	answer_msg = None
	if commission := qiwi.check_commission(**details):
		amount = details['amount'] + commission
		context.user_data['balance'] = database.getUser(user_id)['balance']
		if qiwi.check_balance() < amount:
			answer_msg = menu['input']['msg_error']
			context.bot.send_message(
				config.admin_group_id, texts.qiwi_is_empty,
				reply_markup=InlineKeyboardMarkup(
					[[InlineKeyboardButton(texts.goto_qiwi, url=config.qiwi_url)]])
			)
		elif context.user_data['balance'] >= amount and (payment_id := qiwi.make_payment(**details)):
			answer_msg = menu['input']['msg_success']
			context.user_data['balance'] = database.updateBalance(user_id, -amount, payment_id)
	del context.user_data['withdraw_details']
	update.callback_query.answer(answer_msg or menu['input']['msg_fail'], show_alert=True)


def withdrawFunds(update, context, menu=profile_menu['next']['withdraw_funds']):
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
			confirm_button = [InlineKeyboardButton(
				texts.confirm, callback_data=f'confirm_withdraw')]
			commission_warning = menu['input']['msg_valid'].format(
				commission, details['amount'] + commission)
	return (
		menu['msg'].format(
			balance=context.user_data['balance'],
			**{key: value or menu['default'] for key, value in details.items()}
		) + commission_warning,
		[confirm_button] + menu['buttons']
	)


def getWithdrawProvider(update, context, menu):
	if details := context.user_data.get('withdraw_details'):
		details['provider'] = update.callback_query.data
	del context.user_data['history'][-2:]
	return withdrawFunds(update, context)


@withInput
def getWithdrawAccount(update, context, menu, user_input, validated):
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


@withInput
def getWithdrawAmount(update, context, menu, user_input, validated):
	if not validated:
		return re.match(r'^[1-9][0-9]{1,4}$', user_input)

	if not (details := context.user_data.get('withdraw_details')):
		return False
	if (amount := int(user_input)) > context.user_data['balance']:
		return False

	details['amount'] = amount
	return True
