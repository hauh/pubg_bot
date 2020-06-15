"""Various utility classes and functions"""

from telegram import InlineKeyboardButton
from telegram.error import TelegramError

import texts
import config

##############################


class MessagesList(list):
	"""Holds message promises to check or clean them later"""

	def delete_all(self):
		for msg_promise in self:
			try:
				msg_promise.result().delete()
			except TelegramError:
				continue
			except AttributeError:  # if it was an actual message, not a Promise
				msg_promise.delete()
		self.clear()


class Conversation:
	"""Holds user's history for MenuHandler, and previous messages to clean"""

	def __init__(self):
		self.history = ['_main_']
		self.messages = MessagesList()

	def __str__(self):
		return str(self.history)

	def back(self, level=1):
		del self.history[-level:]
		if not self.history:
			self.history = ['_main_']
		return self.history[-1]

	def repeat(self):
		return self.history[-1]

	def restart(self):
		self.history = ['_main_']
		return self.history[0]

	def next(self, state):
		self.history.append(state)
		return state


def button(callback_data, text):
	return [InlineKeyboardButton(text, callback_data=callback_data)]


def confirm_button(callback_data, text=texts.confirm):
	return button(f'_confirm_{callback_data}', text)


def notify(users, text, context, *, expires=None):
	messages = MessagesList()
	for user_id in users:
		messages.append(context.bot.send_message(user_id, text))
	if expires:
		context.job_queue.run_once(
			lambda c: c.job.context.delete_all(),
			expires, context=messages
		)


def notify_admins(text, context, *, expires=None):
	notify([config.admin_group_id], text, context, expires=expires)
