"""Custom Handler to work with tree-like menu dict with texts and callbacks"""

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import Handler
from telegram.error import BadRequest

###################


class Conversation:
	"""Holds `State` of conversation with user, response, and old messages"""

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
	"""Handler for private conversations, duh."""

	def __init__(self, dialogue_tree):
		super().__init__(callback=None)
		self.start = dialogue_tree
		self.user_conversations = dict()

	def check_update(self, update):
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

		# cleaning up previous messages
		for message in conversation.messages:
			message.delete()
		conversation.messages.clear()

		text, buttons, answer = conversation.state(conversation, context)

		# sending reponse
		if answer:
			update.callback_query.answer(**answer)
		update.effective_chat.send_message(
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
