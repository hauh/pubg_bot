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


def splitMessageText(text):
	messages = []
	i = 0
	while i + constants.MAX_MESSAGE_LENGTH < len(text):
		max_lines_index = text.rfind('\n', i, i + constants.MAX_MESSAGE_LENGTH)
		messages.append(text[i:max_lines_index])
		i = max_lines_index + 1
	messages.append(text[i:])
	return messages


def cleanChat(chat_data):
	if 'old_messages' in chat_data:
		for message in chat_data['old_messages']:
			try:
				message.delete()
			except Exception:
				pass


def sendMessage(update, context, message_text, buttons, next_state=None):
	cleanChat(context.chat_data)
	sent_messages = []
	messages = splitMessageText(message_text)
	for message in messages:
		sent_messages.append(
			update.effective_chat.send_message(
				message,
				reply_markup=InlineKeyboardMarkup(buttons)
					if message == messages[-1] else None
			)
		)
	context.chat_data['old_messages'] = sent_messages
	if next_state and next_state not in context.chat_data['conv_history']:
		context.chat_data['conv_history'].append(next_state)
	return next_state


def mainMenu(update, context):
	context.chat_data['conv_history'] = []
	user_id = int(update.effective_user.id)
	chat_id = int(update.effective_chat.id)
	username = update.effective_user.username
	user = database.getUser(user_id)
	if not user or user['chat_id'] != chat_id or user['username'] != username:
		database.saveUser(user_id, chat_id, username)
		user = database.getUser(user_id)
	context.user_data.update(user)
	sendMessage(
		update, context,
		texts.menu['msg'],
		texts.menu['buttons'] if user_id in config.admin_id
			else texts.menu['buttons'][1:],
		'main'
	)
	return -1


def back(update, context):
	if len(context.chat_data['conv_history']) < 2:
		return mainMenu(update, context)
	context.chat_data['conv_history'].pop()
	update.callback_query.data = context.chat_data['conv_history'][-1]
	return context.dispatcher.process_update(update)


class MenuHandler(Handler):

	def __init__(self, menu):
		self.menu = menu
		super(MenuHandler, self).__init__(callback=None)

	def check_update(self, update):
		if isinstance(update, Update) and update.effective_chat.type == 'private':
			return True
		return False

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
		if not update.callback_query:
			return update.effective_message.delete()
		else:
			next_state = update.callback_query.data
		menu = self._findMenu(self.menu, next_state)
		if not menu:
			return mainMenu(update, context)
		return sendMessage(update, context, menu['msg'], menu['buttons'], next_state)
