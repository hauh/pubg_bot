from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import texts
import config

##############################


def getButton(text, callback_data):
	return [InlineKeyboardButton(text, callback_data=callback_data)]


def confirmButton(callback_data):
	return getButton(texts.confirm, f'confirm_{callback_data}')


admin_warnings = {
	'qiwi_failed': {
		'text': texts.qiwi_error,
		'reply_markup': InlineKeyboardMarkup(
			[[InlineKeyboardButton(texts.goto_qiwi, url=config.qiwi_url)]])
	},
	'prizes': {
		'text': texts.match_has_ended
	},
}


def message_admins(bot, status, **format_kwargs):
	message = admin_warnings[status]
	bot.send_message(
		config.admin_group_id,
		message['text'].format(**format_kwargs),
		reply_markup=message.get('reply_markup')
	)
