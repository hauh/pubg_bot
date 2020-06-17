"""Various utility classes and functions"""

from telegram import InlineKeyboardButton

from pubglik.bot.texts import confirm as CONFIRM_TEXT

##############################


class Conversation:
	"""Holds user's history for MenuHandler, and previous messages to clean"""

	def __init__(self):
		self.history = ['_main_']
		self.messages = []

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


def confirm_button(callback_data, text=CONFIRM_TEXT):
	return button(f'_confirm_{callback_data}', text)
