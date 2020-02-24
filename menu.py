from telegram import (
	Update, ParseMode,
	InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import Handler
import texts as txt

###################


def createButton(button_msg, button_key):
	return InlineKeyboardButton(
		button_msg,
		callback_data=button_key
	)


def createKeyboard(reply_menu):
	choices = []
	if 'next' in reply_menu:
		for button_key, button_data in reply_menu['next'].items():
			choices.append([createButton(button_data['btn'], button_key)])
	if reply_menu != txt.menu:
		navigation = [
			createButton(txt.back, 'back'),
			createButton(txt.main, 'main'),
		]
		choices.append(navigation)
	return InlineKeyboardMarkup(choices)


class MenuHandler(Handler):

	def __init__(self, menu):
		self.menu = menu
		super(MenuHandler, self).__init__(callback=None)

	def _findMenu(self, menu, state):
		try:
			return menu['next'][state]
		except KeyError:
			if 'next' in menu:
				for next_menu in menu['next']:
					deeper_result = self._findMenu(menu['next'][next_menu], state)
					if deeper_result:
						return deeper_result
		return None

	def check_update(self, update):
		return True if isinstance(update, Update) else False

	def _sendMessage(self, update, state, reply_menu):
		if update.callback_query:
			update.callback_query.message.delete()
		update.effective_chat.send_message(
			reply_menu['msg'],
			parse_mode=ParseMode.MARKDOWN,
			reply_markup=createKeyboard(reply_menu)
		)
		return state

	def handle_update(self, update, dispatcher, check_result, context=None):
		if not update.callback_query:
			next_state = context.user_data['conv_history'][-1]
		elif update.callback_query.data != 'back':
			next_state = update.callback_query.data
			if next_state == 'main':
				context.user_data['conv_history'] = ['main']
			else:
				context.user_data['conv_history'].append(next_state)
		else:
			context.user_data['conv_history'].pop()
			next_state = context.user_data['conv_history'][-1]
		reply_menu = self._findMenu(self.menu, next_state)
		if not reply_menu:
			reply_menu = self.menu
			context.user_data['conv_history'] = ['main']
		return self._sendMessage(update, next_state, reply_menu)
