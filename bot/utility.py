'''Various common helper functions'''

from telegram import InlineKeyboardButton
from telegram.error import TelegramError

import texts
import config

##############################


def button(callback_data, text):
	return [InlineKeyboardButton(text, callback_data=callback_data)]


def confirm_button(callback_data, text=texts.confirm):
	return button(f'_confirm_{callback_data}', text)


def notify(users, text, context, *, expires=None):
	messages = []
	for user_id in users:
		messages.append(context.bot.send_message(user_id, text))
	if expires:
		context.job_queue.run_once(_delete_messages, expires, context=messages)


def notify_admins(text, context, *, expires=None):
	notify([config.admin_group_id], text, context, expires=expires)


def _delete_messages(context):
	for message_promise in context.job.context:
		try:
			msg = message_promise.result()
		except TelegramError:
			continue
		msg.delete()
