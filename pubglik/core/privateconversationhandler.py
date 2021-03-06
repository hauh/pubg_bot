"""Custom `Handler`, builds menu from tree and keeps track of conversations."""

from telegram import InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import Handler

###################


class State:
	"""Node of dialogue tree with menu options appropriate to that node."""

	main_button = back_button = confirm_button = None

	@classmethod
	def build_tree(cls, menu_tree, menu_data):
		cls.main_button = menu_data['buttons']['_main_']
		cls.back_button = menu_data['optional_buttons']['_back_']
		cls.confirm_button = staticmethod(menu_data['optional_buttons']['_confirm_'])
		return cls(menu_tree, '_main_', None, menu_data)

	def __init__(self, current_menu, key, previous_state, menu_data):
		self.key = key
		self.back = previous_state
		self.texts = menu_data['texts'].get(key, "MISSING TEXT")
		self.answers = menu_data['answers'].get(key)
		self.callback = menu_data['callbacks'].get(key)
		self.extra = menu_data['optional_buttons'].get(key, {})
		self.buttons = []
		self.next = {}
		for next_key, submenu in current_menu.items():
			self.next[next_key] = State(submenu, next_key, self, menu_data)
			if next_button := menu_data['buttons'].get(next_key):
				self.buttons.append(next_button)

	def __call__(self, conversation, context):
		if self.callback:
			return self.callback(self, conversation, context)
		return conversation.reply(self.texts)

	def __repr__(self):
		return f"State '{self.key}'"


class Conversation:
	"""Holds `State` of conversation with user, and processes `State`s callback
	with new data from `Update`."""

	def __init__(self, starting_state, user_id):
		self.user_id = user_id
		self.state = starting_state
		self.banned = False
		self.messages = []

		self.update = None
		self.input = None
		self.confirmed = False

	def __repr__(self):
		return f"<Conversation: {repr(self.state)}>"

	def back(self, context, answer=None):
		self.input = None
		self.confirmed = False
		if answer:
			answer = self.state.answers[answer]
		self.state = self.state.back
		text, buttons, back_answer = self.state(self, context)
		return text, buttons, answer or back_answer

	def reply(self, text=None, extra_buttons=(), answer=None, confirm=None):
		buttons = []
		if confirm:
			buttons.append(self.state.confirm_button(confirm))
		buttons += self.state.buttons
		buttons += extra_buttons
		if self.state.back:
			buttons.append(
				self.state.back_button if not self.state.back.back
				else (self.state.back_button + self.state.main_button)
			)
		if answer:
			try:
				answer = self.state.answers[answer]
			except KeyError:
				answer = {'text': answer, 'show_alert': True}
		return text or self.state.texts, buttons, answer


class PrivateConversationHandler(Handler):
	"""Processes updates from users and keeps track of `Conversations` with them.
	On `__init__` creates tree of menu `State`s, and for each new user creates
	`Conversation` for them to hold their current `State`.

	Attributes:
		start (State): Starting `State` of menu tree.
		user_conversations (dict): The `dict` with all ongoing `Conversations`.
	"""

	def __init__(self, menu_tree, menu_data):
		"""
		Args:
			menu_tree (dict): A (nested) `dict` with menu structure.
			menu_data (dict): A `dict` with 'callbacks', 'texts', 'answers',
				'buttons', and 'optional_buttons' keys for `States` of menu tree.
		"""

		super().__init__(callback=None)
		self.start = State.build_tree(menu_tree, menu_data)
		self.user_conversations = dict()

	def check_update(self, update):
		"""Checks if incoming update is for this handler to handle. If it is,
		advances `State` of `Conversation`."""

		if not isinstance(update, Update) or update.effective_chat.type != 'private':
			return False

		conversation = self.user_conversations.setdefault(
			update.effective_user.id,
			Conversation(self.start, update.effective_user.id)
		)
		if conversation.banned:
			return False

		# if update is from button
		if query := update.callback_query:
			next_state, *user_input = query.data.split(';')  # buttons: menu;data
			user_input = "".join(user_input).strip()
			try:
				query.message.edit_reply_markup(reply_markup=None)
			except BadRequest:  # double click
				return False

		# else from input
		elif message := update.effective_message:
			next_state = None
			user_input = message.text.strip() if message.text else None

		else:
			return False

		# determining next conversation state
		if next_state == '_back_':
			conversation.state = conversation.state.back or conversation.state
		elif next_state == '_main_':
			while conversation.state.back:
				conversation.state = conversation.state.back
		elif next_state == '_confirm_':
			conversation.confirmed = True
		elif next_state in conversation.state.next:
			conversation.state = conversation.state.next[next_state]

		conversation.update = update
		conversation.input = user_input

		return conversation

	def handle_update(self, update, dispatcher, conversation, context):
		"""Cleans chat, gets next message from `State`, and sends it to user."""

		text, buttons, answer = conversation.state(conversation, context)

		if answer:
			update.callback_query.answer(**answer)

		# cleaning up previous messages
		for message in conversation.messages:
			message.delete()
		conversation.messages.clear()

		# sending reponse
		dispatcher.bot.send_message(
			update.effective_chat.id,
			text or self.state.texts,
			reply_markup=InlineKeyboardMarkup(buttons) if any(buttons) else None,
			container=conversation.messages
		)

		# cleaning up
		conversation.update = None
		conversation.input = None
		conversation.confirmed = False
		if not update.callback_query:
			update.effective_message.delete()
		context.user_data['conversation'] = conversation
