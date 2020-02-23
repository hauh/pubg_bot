import re

from telegram import Update, ParseMode
from telegram.ext import Handler, ConversationHandler, CommandHandler

###################


class MenuHandler(Handler):

	def __init__(self, main_menu, submenu):
		self.main_menu = main_menu
		self.menu = submenu
		self.pattern = r'^({})|(back)|(main)$'.format(')|('.join(submenu.keys()))
		super(MenuHandler, self).__init__(callback=None)

	def _showMenu(self, update, context, reply_options):
		update.callback_query.edit_message_text(
			reply_options['message'],
			parse_mode=ParseMode.MARKDOWN,
			reply_markup=reply_options['keyboard']
		)
		context.user_data['conv_level'] = state
		return state

	def check_update(self, update):
		return True if isinstance(update, Update) else False

	def handle_update(self, update, dispatcher, check_result, context=None):
		data = update.callback_query.data
		try:
			if not data:
				reply_options = self.menu[context.user_data['conv_level']]
			elif data == 'main':
				reply_options = self.main_menu
			elif data == 'back':
				reply_options = self.menu[self.menu[data]['back']]
			else:
				reply_options = self.menu[data]
		except KeyError:
			reply_options = self.main_menu
		return self._showMenu(update, context, reply_options)


def stop(update, context):
	del context.user_data['conv_level']
	return ConversationHandler.END


def createConversationHandler(main_menu, submenu):
	return ConversationHandler(
		entry_points=[
			MenuHandler(main_menu, submenu)
		],
		states={
			key: [MenuHandler(main_menu, submenu)] for key in submenu.keys()
		},
		map_to_parent={
			ConversationHandler.END: 'main',
		},
		fallbacks=[
			CommandHandler('stop', stop)
		],
		conversation_timeout=1200
	)
