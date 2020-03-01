from logging import getLogger

from telegram import Update, CallbackQuery, ParseMode, InlineKeyboardMarkup
from telegram.ext import Handler

import config
import texts
import database

###################

logger = getLogger(__name__)


def sendMessage(update, context, message, buttons, next_state=None):
	if '_previous_messages' in context.user_data:
		for message in context.user_data['_previous_messages']:
			try:
				message.delete()
			except Exception:
				pass
	previous_messages = []
	previous_messages.append(
		update.effective_chat.send_message(
			message,
			parse_mode=ParseMode.MARKDOWN,
			reply_markup=InlineKeyboardMarkup(buttons)
		)
	)
	# previous_messages[-1].edit_reply_markup(InlineKeyboardMarkup(buttons))
	context.user_data['_previous_messages'] = previous_messages
	if next_state and next_state not in context.user_data['conv_history']:
		context.user_data['conv_history'].append(next_state)
	return next_state


def mainMenu(update, context):
	context.user_data['conv_history'] = []
	if 'pubg_id' not in context.user_data:
		_, context.user_data['pubg_id'], context.user_data['balance'] =\
			database.getUser(update.effective_user.id).values()
	sendMessage(
		update, context,
		texts.menu['msg'],
		texts.menu['buttons'] if update.effective_user.id in config.admin_id
			else texts.menu['buttons'][1:],
		'main'
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
			return update.effective_message.delete()
		else:
			next_state = update.callback_query.data
		menu = self._findMenu(self.menu, next_state)
		if not menu:
			return mainMenu(update, context)
		return sendMessage(update, context, menu['msg'], menu['buttons'], next_state)
