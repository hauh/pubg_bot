'''Avoiding flood limits'''

from telegram.bot import Bot as PTBot
from telegram.ext.messagequeue import queuedmessage
from telegram.error import BadRequest

##############################


class Bot(PTBot):
	'''Sends all messages through timed queue'''

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

	def delete_message(self, *args, **kwargs):
		try:
			super().delete_message(*args, **kwargs)
		except BadRequest:
			pass
