import config

from telegram import (
	Update, ParseMode,
	InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import Handler

import texts

###################


def createButton(button_msg, button_key):
	return InlineKeyboardButton(
		button_msg,
		callback_data=button_key
	)


def createKeyboard(menu, extra):
	choices = []
	if 'next' in menu:
		for button_key, button_data in menu['next'].items():
			choices.append([createButton(button_data['btn'], button_key)])
	for button_key, button_data in extra.items():
		choices.append([createButton(button_data['btn'], button_key)])
	if menu != texts.menu:
		navigation = [
			createButton(texts.back, 'back'),
			createButton(texts.main, 'main'),
		]
		choices.append(navigation)
	return InlineKeyboardMarkup(choices)


def sendMessage(update, context, next_state, menu, extra={}, msg_format={}):
	if update.callback_query:
		update.callback_query.message.delete()
	update.effective_chat.send_message(
		menu['msg'].format(**msg_format),
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=createKeyboard(menu, extra)
	)
	if next_state not in context.user_data['conv_history']:
		context.user_data['conv_history'].append(next_state)
	return next_state


def mainMenu(update, context):
	context.user_data['conv_history'] = []
	sendMessage(
		update, context, 'main', texts.menu,
		extra=texts.admin_option
			if update.effective_user.id in config.admin_id else {}
	)
	return -1


def back(update, context):
	if len(context.user_data['conv_history']) < 2:
		return mainMenu(update, context)
	context.user_data['conv_history'].pop()
	update.callback_query.data = context.user_data['conv_history'].pop()
	return context.dispatcher.process_update(update)


class MenuHandler(Handler):

	def __init__(self, menu):
		self.menu = menu
		super(MenuHandler, self).__init__(callback=None)

	def check_update(self, update):
		return True if isinstance(update, Update) else False

	def _findMenu(self, menu, next_state):
		try:
			return menu['next'][next_state]
		except KeyError:
			if 'next' in menu:
				for next_menu in menu['next']:
					deeper_result = self._findMenu(menu['next'][next_menu], next_state)
					if deeper_result:
						return deeper_result
		return None

	def handle_update(self, update, dispatcher, check_result, context=None):
		print(update.callback_query.data)
		if not update.callback_query:
			next_state = context.user_data['conv_history'][-1]
		else:
			next_state = update.callback_query.data
		menu = self._findMenu(self.menu, next_state)
		if not menu:
			return mainMenu(update, context)
		return sendMessage(update, context, next_state, menu)
