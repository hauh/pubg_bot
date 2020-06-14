'''Custom bot with Message Queue for avoiding flood, and logging exceptions'''

import logging

from telegram.bot import Bot as PTBot
from telegram.ext.messagequeue import queuedmessage
from telegram.error import BadRequest

##############################

logger = logging.getLogger('bot')


class Bot(PTBot):
	'''Sends all messages through timed queue, logs requests errors'''

	def __init__(self, *args, msg_queue, **kwargs):
		super().__init__(*args, **kwargs)
		self._is_messages_queued_default = True
		self._msg_queue = msg_queue

	def __del__(self):
		try:
			self._msg_queue.stop()
		except RuntimeError:
			pass

	@queuedmessage
	def send_message(self, *args, **kwargs):
		return super().send_message(*args, **kwargs)

	def delete_message(self, chat_id, *args, **kwargs):
		try:
			super().delete_message(chat_id, *args, **kwargs)
		except BadRequest as err:
			logger.error(
				"Deleting message in chat %s failed", chat_id,
				exc_info=(type(err), err, None)
			)

	def answer_callback_query(self, callback_query_id, text=None, **kwargs):
		try:
			super().answer_callback_query(callback_query_id, text, **kwargs)
		except BadRequest as err:
			logger.error(
				"Answering query id %s (%s) failed", callback_query_id, text,
				exc_info=(type(err), err, None)
			)
