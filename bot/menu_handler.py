'''Custom Handler designed to work with menu dictionary from texts.py'''

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import Handler
from telegram.error import BadRequest
from telegram.constants import MAX_MESSAGE_LENGTH

###################


class MenuHandler(Handler):
	'''
	If there is callback_data from button MenuHandler will search for callback
	in self.menu. That callback should return message and buttons. If there is
	no callback in menu, MenuHandler will use messsage from menu for that
	button. There are special cases: '_back_', '_main_', and '_confirm_'. The
	latter fills 'validated_input' with whatever else was with 'confirm' and
	calls previous callback. If there is a message from user, handler fills
	'user_input' in user_data and calls previous callback.
	'''

	def __init__(self, menu):
		self.menu = menu
		super(MenuHandler, self).__init__(callback=None)

	@staticmethod
	def send_message(update, text, buttons, old_messages):
		'''Sending message in chunks if it's too big splitted by newlines'''
		# first cleaning up old messages
		for message in old_messages:
			try:
				message.delete()
			except BadRequest:
				pass
		old_messages.clear()

		# then partitioning text
		messages, i = [], 0
		while i + MAX_MESSAGE_LENGTH < len(text):
			max_lines_index = text.rfind('\n', i, i + MAX_MESSAGE_LENGTH)
			messages.append(text[i:max_lines_index])
			i = max_lines_index + 1
		messages.append(text[i:])

		# finally sending and storing messages to delete next time
		for message in messages:
			old_messages.append(update.effective_chat.send_message(message))
		if buttons and any(buttons):
			old_messages[-1].edit_reply_markup(
				reply_markup=InlineKeyboardMarkup(buttons))

	@staticmethod
	def check_update(update):
		if not isinstance(update, Update):
			return False
		if update.effective_chat.type != 'private':
			return False
		return True

	def handle_update(self, update, dispatcher, check_result, context):
		history = context.user_data.setdefault('history', ['_main_'])
		old_messages = context.user_data.setdefault('old_messages', [])

		# determining next state
		if update.callback_query:
			next_state = MenuHandler._read_query(update, context, history)
		else:
			old_messages.append(update.effective_message)
			next_state = MenuHandler._read_message(update, context, history)

		# updating user history with next state or trimming history if back
		try:
			del history[history.index(next_state) + 1:]
		except ValueError:
			history.append(next_state)

		# getting message and buttons for next state
		if (next_state == '_main_'
		or not (menu := MenuHandler._find_menu(next_state, self.menu))):
			menu = self.menu
		if 'callback' in menu:
			text, buttons = menu['callback'](update, context, menu)
		else:
			text, buttons = menu['msg'], menu['buttons']

		# clearing user_input
		context.user_data.pop('user_input', None)
		context.user_data.pop('validated_input', None)

		if text:
			MenuHandler.send_message(update, text, buttons, old_messages)

	@staticmethod
	def _read_query(update, context, history):
		try:
			update.callback_query.message.edit_reply_markup(
				reply_markup=InlineKeyboardMarkup([[]]))
		except BadRequest:
			pass
		if update.callback_query.data == '_back_':
			return history[-2]
		if update.callback_query.data.startswith('_confirm_'):
			context.user_data['validated_input'] =\
				update.callback_query.data.replace('_confirm_', '')
			return history[-1]
		return update.callback_query.data

	@staticmethod
	def _read_message(update, context, history):
		if (message := update.effective_message).text:
			context.user_data['user_input'] = message.text
		else:
			context.user_data['user_input'] = message.effective_attachment
		return history[-1]

	@staticmethod
	def _find_menu(next_state, menu):
		for next_menu_key, next_menu in menu.get('next', {}).items():
			if next_state.startswith(next_menu_key):
				return next_menu
			if deeper_result := MenuHandler._find_menu(next_state, next_menu):
				return deeper_result
		return None
