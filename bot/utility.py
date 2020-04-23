from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import texts
import config

##############################


def getButton(text, callback_data):
	return [InlineKeyboardButton(text, callback_data=callback_data)]


def confirmButton(callback_data):
	return getButton(texts.confirm, f'confirm_{callback_data}')


def messageAdmins(bot, message_text):
	bot.send_message(config.admin_group_id, message_text)
