'''Avoiding flood limits'''

from telegram.bot import Bot as BaseBot
from telegram.ext.messagequeue import MessageQueue, queuedmessage

##############################


class Bot(BaseBot):
	'''Sends all messages through timed queue'''

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._is_messages_queued_default = True
		self._msg_queue = MessageQueue(all_burst_limit=29, all_time_limit_ms=1017)

	def __del__(self):
		try:
			self._msg_queue.stop()
		except RuntimeError:
			pass

	@queuedmessage
	def send_message(self, *args, **kwargs):
		return super().send_message(*args, **kwargs)
