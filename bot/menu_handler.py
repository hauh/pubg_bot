import re

from telegram import (
	constants, Update, CallbackQuery, InlineKeyboardMarkup
)
from telegram.ext import Handler

###################

class MenuHandler(Handler):

	def __init__(self, menu):
		self.menu = menu
		super(MenuHandler, self).__init__(callback=None)

	@staticmethod
	def cleanChat(old_messages):
		for message in old_messages:
			try:
				message.delete()
			except Exception:
				pass
		old_messages.clear()

	def check_update(self, update):
		if isinstance(update, Update) and update.effective_chat.type == 'private':
			return True
		return False

	def handle_update(self, update, dispatcher, check_result, context):
		# hiding buttons
		if update.callback_query:
			try:
				update.callback_query.message.edit_reply_markup(
					reply_markup=InlineKeyboardMarkup([[]]))
			except Exception:
				pass

		history = context.user_data.setdefault('history', ['main'])
		next_state = self._getNextState(update, context, history)

		if next_state in history:
			del history[history.index(next_state) + 1:]
		else:
			history.append(next_state)

		if not (menu := self._findMenu(next_state)):
			menu = self.menu
		if 'callback' in menu:
			text, *buttons = menu['callback'](update, context, menu)
		else:
			text, *buttons = (menu['msg'],)
		if 'buttons' in menu:
			buttons += menu['buttons']

		context.user_data.pop('user_input', None)
		if text:
			old_messages = context.user_data.setdefault('old_messages', [])
			MenuHandler.cleanChat(old_messages)
			self._sendMessage(update, context, text, buttons, old_messages)

	def _getNextState(self, update, context, history):
		# if from button
		if update.callback_query.data:
			if update.callback_query.data == 'back':
				del history[-1]
				return history[-1]
			elif re.match(r'^confirm', update.callback_query.data):
				context.user_data['validated_input'] = re.sub(
					r'^confirm_', '', update.callback_query.data)
				return history[-1]
			return update.callback_query.data

		# elif from message
		message = update.effective_message
		context.user_data['old_messages'].append(message)
		if not message.text:
			context.user_data['user_input'] = message.effective_attachment
		elif message.text == '/start':
			return 'main'
		elif message.text == '/admin':
			return 'admin'
		else:
			context.user_data['user_input'] = message.text
		return history[-1]

	def _findMenu(self, next_state, menu=None):
		if menu is None:
			menu = self.menu
		for next_menu_key, next_menu in menu.get('next', {}).items():
			if re.match(next_menu_key, next_state):
				return next_menu
			if deeper_result := self._findMenu(next_state, next_menu):
				return deeper_result
		return None

	def _sendMessage(self, update, context, text, buttons, old_messages):
		messages = []
		i = 0
		while i + constants.MAX_MESSAGE_LENGTH < len(text):
			max_lines_index = text.rfind('\n', i, i + constants.MAX_MESSAGE_LENGTH)
			messages.append(text[i:max_lines_index])
			i = max_lines_index + 1
		messages.append(text[i:])
		for message in messages:
			old_messages.append(update.effective_chat.send_message(message))
		old_messages[-1].edit_reply_markup(
			reply_markup=InlineKeyboardMarkup(buttons))
