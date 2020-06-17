"""Custom Handler to work with tree-like menu dict with texts and callbacks"""

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import Handler
from telegram.error import BadRequest
from telegram.constants import MAX_MESSAGE_LENGTH

from .utility import Conversation

###################


class MenuHandler(Handler):
	"""Works both with regular messages and callback data (from inline buttons).

	Attributes:
		menu (`dict`): Menu dictionary in following format:
			'msg': Template of text to message user;
			'buttons': Array of inline Telegram buttons;
			'callback': Function to run with update. If present it should return
				text and buttons instead;
			'next: `dict` of submenus in same format;
			Any other fields (like 'answers' for answering callback query with),
				to use in callback.

		If update is a `CallbackQuery`, the hadler will determine next action based
	on `callback_query.data` and user's history in :obj:`UserConversation`:
		'_main_': Returns to main menu (top level of `menu` dict);
		'_back_': Returns to previous level;
		'_confirm_[data]': Returns same callback as last time, but now with user
			`data` extracted from callback data as validated user input;
		`anything_other`: Handler will look for submenu with same key as callback
			data in `menu` dict. If such key is not present, returns to main menu,
			if 'callback' is not present, sends message with 'msg' and 'buttons'
			from that menu, otherwise gets text and buttons from callback.

		If update is a `Message`, the handler will store it as user input (to
	use in callback, for example to generate confirm button with this input),
	and	repeats same callback.
	"""

	def __init__(self, menu):
		self.menu = menu
		super().__init__(callback=None)

	@staticmethod
	def send_message(chat, conversation, text, buttons=[]):
		"""Sending message (in chunks if it's too big) after deleting previous"""

		conversation.messages.delete_all()

		while len(text) > MAX_MESSAGE_LENGTH:
			if (i_max := text.rfind('\n', end=MAX_MESSAGE_LENGTH)) == -1:
				i_max = text.rfind(' ', end=MAX_MESSAGE_LENGTH)
			conversation.messages.append(chat.send_message(text[:i_max]))
			text = text[i_max + 1:]

		keyboard = InlineKeyboardMarkup(buttons) if any(buttons) else None
		conversation.messages.append(chat.send_message(text, reply_markup=keyboard))

	@staticmethod
	def check_update(update):
		if not isinstance(update, Update):
			return False
		if update.effective_chat.type != 'private':
			return False
		return True

	def handle_update(self, update, dispatcher, check_result, context):
		conversation = context.user_data.setdefault('conversation', Conversation())

		# if update is from button
		if cbq := update.callback_query:

			# removing buttons to prevent clicking again
			try:
				cbq.message.edit_reply_markup(reply_markup=None)
			except BadRequest:
				pass

			# parsing button data
			if cbq.data == '_back_':
				next_state = conversation.back()
			elif cbq.data == '_main_':
				next_state = conversation.restart()
			elif cbq.data.startswith('_confirm_'):
				next_state = conversation.repeat()
				context.user_data['validated_input'] = cbq.data[9:]
			else:
				next_state = conversation.next(cbq.data)

		# else from input
		else:
			msg = update.effective_message
			context.user_data['user_input'] = msg.text or msg.effective_attachment
			msg.delete()
			next_state = conversation.repeat()

		# getting message and buttons for next state
		if not (menu := self._find_menu(next_state, self.menu)):
			menu = self.menu
		if 'callback' in menu:
			text, buttons = menu['callback'](update, context, menu)
		else:
			text, buttons = menu['msg'], menu['buttons']

		# clearing user_input
		context.user_data.pop('user_input', None)
		context.user_data.pop('validated_input', None)

		self.send_message(update.effective_chat, conversation, text, buttons)

	@staticmethod
	def _find_menu(next_state, menu):
		for next_menu_key, next_menu in menu.get('next', {}).items():
			if next_state.startswith(next_menu_key):
				return next_menu
			if deeper_result := MenuHandler._find_menu(next_state, next_menu):
				return deeper_result
		return None
