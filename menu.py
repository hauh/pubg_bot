from logging import getLogger

from telegram import (
	constants, Update, CallbackQuery, InlineKeyboardMarkup
)
from telegram.ext import Handler

import config
import texts
import database

###################

logger = getLogger(__name__)


class MenuHandler(Handler):

	def __init__(self, menu, callbacks_lists):
		self.menu = menu
		self.callbacks = {}
		for callback_list in callbacks_lists:
			self.callbacks.update(callback_list)
		super(MenuHandler, self).__init__(callback=None)

	def check_update(self, update):
		if isinstance(update, Update) and update.effective_chat.type == 'private':
			return True
		return False

	def handle_update(self, update, dispatcher, check_result, context):
		if 'history' not in context.chat_data:
			context.chat_data['history'] = []
		history = context.chat_data['history']
		print(history)

		next_state = self._getNextState(update, context, history)
		callback = self._findCallback(next_state)
		if callback:
			text, buttons = callback(update, context)
		else:
			menu = self._findMenu(self.menu, next_state)
			if not menu:
				menu = self.menu
			text, buttons = menu['msg'], menu['buttons']

		self._cleanChat(context.chat_data)
		messages = self._splitText(text)
		self._sendMessages(update, context, messages, buttons)
		if next_state in history:
			del history[history.index(next_state) + 1:]
		else:
			history.append(next_state)
		print(history)
		print('\n')

	def _getNextState(self, update, context, history):
		if update.callback_query:
			if update.callback_query.data == 'back':
				if len(history) > 1:
					history.pop()
				return history[-1]
			return update.callback_query.data
		user_input = update.effective_message.text
		update.effective_message.delete()
		if not user_input or user_input == '/start' or len(history) == 0:
			return 'main'
		context.chat_data['user_input'] = user_input
		return history[-1]

	def _findCallback(self, next_state):
		callback = self.callbacks.get(next_state, None)
		if not callback:
			for key in self.callbacks.keys():
				if next_state.startswith(key):
					return self.callbacks[key]
		return callback

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

	def _cleanChat(self, chat_data):
		if 'old_messages' in chat_data:
			for message in chat_data['old_messages']:
				try:
					message.delete()
				except Exception:
					pass

	def _splitText(self, text):
		messages = []
		i = 0
		while i + constants.MAX_MESSAGE_LENGTH < len(text):
			max_lines_index = text.rfind('\n', i, i + constants.MAX_MESSAGE_LENGTH)
			messages.append(text[i:max_lines_index])
			i = max_lines_index + 1
		messages.append(text[i:])
		return messages

	def _sendMessages(self, update, context, messages, buttons):
		sent_messages = []
		for message in messages:
			sent_messages.append(
				update.effective_chat.send_message(
					message,
					reply_markup=InlineKeyboardMarkup(buttons)
						if message == messages[-1] else None
				)
			)
		context.chat_data['old_messages'] = sent_messages
