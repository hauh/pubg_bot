"""Custom Handler to work with tree-like menu dict with texts and callbacks"""

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import Handler

###################


class Conversation:
	"""Holds `State` of conversation with user, response, and old messages"""

	def __init__(self, starting_state, user_id):
		self.user_id = user_id
		self.state = starting_state
		self.messages = []
		self.response = {}
		self.context = None
		self.data = None
		self.confirmed = False

	def back(self):
		self.data = None
		self.state = self.state.back or self.state

	def next(self, next_state, update_data):
		if next_state == '_back_':
			self.state = self.state.back or self.state
		elif next_state == '_main_':
			while self.state.back:
				self.state = self.state.back
		elif next_state == '_confirm_':
			self.confirmed = True
		elif next_state:
			self.state = self.state.next[next_state]
		self.response['buttons'] = list(self.state.buttons)
		self.data = update_data
		return self.state

	def reply(self, text=None, buttons=None, answer=None):
		if text:
			self.response['text'] = text
		if buttons:
			self.response['buttons'].append(buttons)
		if answer:
			self.response['answer'] = answer
		return self.response

	def clear(self):
		self.response = {}
		for message in self.messages:
			message.delete()
		self.messages.clear()


class PrivateConversationHandler(Handler):
	"""Handler for private conversations, duh."""

	def __init__(self, dialogue_tree):
		super().__init__(callback=None)
		self.tree = dialogue_tree
		self.user_conversations = dict()

	@staticmethod
	def check_update(update):
		if not isinstance(update, Update) or update.effective_chat.type != 'private':
			return False

		# if update is from button
		if query := update.callback_query:
			next_state, *data = query.data.split(';')  # buttons: menu;data
			data = "".join(data)
			query.message.edit_reply_markup(reply_markup=None)

		# else from input
		elif message := update.effective_message:
			next_state, data = None, message.text or message.effective_attachment
			message.delete()

		else:
			return False
		return (next_state, data)  # goes to parsed_update

	def handle_update(self, update, dispatcher, parsed_update, context):

		# changing state
		conversation = self.user_conversations.setdefault(
			update.effective_user.id,
			Conversation(self.tree, int(update.effective_user.id))
		)
		next_state = conversation.next(*parsed_update)

		# preparing response
		if next_state.callback:
			response = next_state.callback(conversation, context)
			text = response['text']
			buttons = response.get('buttons')
			if answer := response.get('answer'):
				update.callback_query.answer(**answer)
		else:
			text, buttons = next_state.texts, next_state.buttons

		# responding
		conversation.clear()
		update.effective_chat.send_message(
			text,
			reply_markup=InlineKeyboardMarkup(buttons) if any(buttons) else None,
			container=conversation.messages
		)
