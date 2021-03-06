"""Custom bot with Message Queue for avoiding flood, and logging exceptions."""

from logging import getLogger

from telegram import ParseMode
from telegram.bot import Bot as PTBot
from telegram.constants import MAX_MESSAGE_LENGTH
from telegram.error import BadRequest
from telegram.utils.promise import Promise

from .debug_mode import TelegramRequestWrapper

##############################

logger = getLogger('bot')


def promised(method):
	def sender(self, *args, **kwargs):
		if not self.msg_queue:
			return method(self, *args, **kwargs)
		promise = Promise(method, (self, *args), kwargs)
		return self.msg_queue(promise, kwargs.get('is_group', False))
	return sender


def partitioned(send):
	def split_text(self, chat_id, text, reply_markup=None, **kwargs):
		while len(text) > MAX_MESSAGE_LENGTH:
			if (i_max := text.rfind('\n', 0, MAX_MESSAGE_LENGTH)) == -1:
				if (i_max := text.rfind(' ', 0, MAX_MESSAGE_LENGTH)) == -1:
					i_max = MAX_MESSAGE_LENGTH
			send(self, chat_id, text[:i_max], reply_markup=None, **kwargs)
			text = text[i_max + 1:]
		return send(self, chat_id, text, reply_markup=reply_markup, **kwargs)
	return split_text


class Bot(PTBot):
	"""Sends all messages through timed queue, logs requests errors."""

	def __init__(self, *args, admin_chat, msg_queue, **kwargs):
		super().__init__(*args, **kwargs)
		self.admin_chat = admin_chat
		self.msg_queue = msg_queue
		self.debug_mode = False
		self.default_parse_mode = ParseMode.MARKDOWN

	def __del__(self):
		try:
			self.msg_queue.stop()
		except RuntimeError:
			pass

	@partitioned
	@promised
	def send_message(self, chat_id, text, parse_mode=None,
					reply_markup=None, container: list = None, **kwargs):
		"""Sending message (in chunks if it's too big), and storing it in optional
		`container` to delete later, after it is processed through MessageQueue.
		"""

		try:
			message = super().send_message(
				chat_id, text,
				parse_mode=parse_mode or self.default_parse_mode,
				reply_markup=reply_markup, **kwargs
			)
		except BadRequest as err:
			logger.error(
				"Sending message %s failed:", (chat_id, text),
				exc_info=(type(err), err, None)
			)
			return None

		if container is not None:
			container.append(message)
		return message

	def delete_message(self, chat_id, message_id, **kwargs):
		try:
			super().delete_message(chat_id, message_id, **kwargs)
		except BadRequest as err:
			logger.error(
				"Deleting message in chat %s failed:", chat_id,
				exc_info=(type(err), err, None)
			)

	def answer_callback_query(self, callback_query_id, text=None, **kwargs):
		try:
			super().answer_callback_query(callback_query_id, text, **kwargs)
		except BadRequest as err:
			logger.error(
				"Answering query id %s (%s) failed:", callback_query_id, text,
				exc_info=(type(err), err, None)
			)

	def notify_admins(self, text, **kwargs):
		return self.send_message(self.admin_chat, text, **kwargs)

	def switch_debug_mode(self):
		"""Wraps original Request, failed requests will be sent to debug server"""
		# pylint: disable=attribute-defined-outside-init
		if self.debug_mode:
			self._request = self._request.saved_handler
			logger.info('Debug mode turned off')
		else:
			self._request = TelegramRequestWrapper(self._request)
			logger.warning('Debug mode turned on')
		self.debug_mode = not self.debug_mode
