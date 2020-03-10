import re
from logging import getLogger

from telegram import (
	constants, Update, CallbackQuery, InlineKeyboardMarkup
)
from telegram.ext import Handler

###################

logger = getLogger(__name__)


class MenuHandler(Handler):

	def __init__(self, menu):
		self.menu = menu
		super(MenuHandler, self).__init__(callback=None)

	def check_update(self, update):
		if isinstance(update, Update) and update.effective_chat.type == 'private':
			return True
		return False

	def handle_update(self, update, dispatcher, check_result, context):
		history = context.user_data.setdefault('history', [])
		if not history:
			next_state = 'main'
		else:
			next_state = self._getNextState(update, context, history)

		if next_state in history:
			del history[history.index(next_state) + 1:]
		else:
			history.append(next_state)

		menu = self._findMenu(self.menu, next_state)
		if not menu:
			menu = self.menu
		if 'callback' in menu:
			text, buttons = menu['callback'](update, context, menu)
		else:
			text, buttons = menu['msg'], menu['buttons']

		context.user_data.pop('user_input', None)
		if text:
			old_messages = context.user_data.setdefault('old_messages', [])
			self._cleanChat(old_messages)
			messages = self._splitText(text)
			self._sendMessages(update, context, messages, buttons, old_messages)

	def _getNextState(self, update, context, history):
		if update.callback_query:
			if update.callback_query.data == 'back':
				if len(history) > 1:
					del history[-1:]
				update.callback_query.data = history[-1]
			elif re.match(r'^confirm', update.callback_query.data):
				context.user_data['validated_input'] =\
					update.callback_query.data.lstrip('confirm_')
				update.callback_query.data = history[-1]
		else:
			message = update.effective_message
			context.user_data['old_messages'].append(message)
			update.callback_query = CallbackQuery(
				0, update.effective_user, update.effective_chat,
				data='main' if message.text == '/start' or len(history) == 0
					else history[-1]
			)
			context.user_data['user_input'] = message.text
		return update.callback_query.data

	def _findMenu(self, menu, next_state):
		if 'next' in menu:
			for next_menu_key, next_menu in menu['next'].items():
				if re.match(next_menu_key, next_state):
					return next_menu
				deeper_result = self._findMenu(next_menu, next_state)
				if deeper_result:
					return deeper_result
		return None

	def _splitText(self, text):
		messages = []
		i = 0
		while i + constants.MAX_MESSAGE_LENGTH < len(text):
			max_lines_index = text.rfind('\n', i, i + constants.MAX_MESSAGE_LENGTH)
			messages.append(text[i:max_lines_index])
			i = max_lines_index + 1
		messages.append(text[i:])
		return messages

	def _cleanChat(self, old_messages):
		for message in old_messages:
			try:
				message.delete()
			except Exception:
				pass
		old_messages.clear()

	def _sendMessages(self, update, context, messages, buttons, old_messages):
		for message in messages:
			old_messages.append(
				update.effective_chat.send_message(
					message,
					reply_markup=InlineKeyboardMarkup(buttons)
						if message == messages[-1] and buttons else None
				)
			)
