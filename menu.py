from logging import getLogger

from telegram import Update, ParseMode, InlineKeyboardMarkup
from telegram.ext import Handler

import config
import texts

###################

logger = getLogger(__name__)


def sendMessage(update, context, next_state, message, buttons):
	if update.callback_query:
		update.callback_query.message.delete()
	update.effective_chat.send_message(
		message,
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=InlineKeyboardMarkup([*buttons])
	)
	if next_state not in context.user_data['conv_history']:
		context.user_data['conv_history'].append(next_state)
	return next_state


def mainMenu(update, context):
	context.user_data['conv_history'] = []
	sendMessage(
		update, context, 'main', texts.main_menu['msg'],
		(texts.main_menu['extra_buttons']
			if update.effective_user.id in config.admin_id else None,
			texts.main_menu['buttons'])
	)
	return -1


def back(update, context):
	if len(context.user_data['conv_history']) < 2:
		return mainMenu(update, context)
	context.user_data['conv_history'].pop()
	update.callback_query.data = context.user_data['conv_history'][-1]
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
			if 'conv_history' in context.user_data:
				next_state = context.user_data['conv_history'][-1]
			else:
				return mainMenu(update, context)
		else:
			next_state = update.callback_query.data
		menu = self._findMenu(self.menu, next_state)
		if not menu:
			return mainMenu(update, context)
		return sendMessage(update, context, next_state, menu)
