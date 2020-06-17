"""Custom bot with Message Queue for avoiding flood, and logging exceptions."""

# pylint: disable=protected-access,attribute-defined-outside-init

from logging import getLogger

from telegram import ParseMode
from telegram.bot import Bot as PTBot
from telegram.utils.promise import Promise
from telegram.error import BadRequest
from telegram.constants import MAX_MESSAGE_LENGTH

from .debug_mode import TelegramRequestWrapper

##############################

logger = getLogger('bot')


class Bot(PTBot):
	"""Sends all messages through timed queue, logs requests errors."""

	def __init__(self, *args, admin_chat, msg_queue, **kwargs):
		super().__init__(*args, **kwargs)
		self.admin_chat = admin_chat
		self._msg_queue = msg_queue
		self.debug_mode = False
		self.default_parse_mode = ParseMode.MARKDOWN

	def __del__(self):
		try:
			self._msg_queue.stop()
		except RuntimeError:
			pass

	@staticmethod
	def check_promise_result(promise):
		try:
			if message := promise.result(timeout=1):
				return message
		except BadRequest as err:
			logger.error(
				"Sending message %s failed:", promise.args,
				exc_info=(type(err), err, None)
			)
		else:
			logger.warning("Message %s hasn't been delivered yet", promise.args)
		return None

	def send_message(self, chat_id, text, *, parse_mode=None,
					reply_markup=None, container=None, is_group=False, **kwargs):
		"""Putting message promises in MessageQueue (in chunks if it's too big),
		storing it in optional `container` to delete later.
		"""

		while len(text) > MAX_MESSAGE_LENGTH:
			if (i_max := text.rfind('\n', end=MAX_MESSAGE_LENGTH)) == -1:
				i_max = text.rfind(' ', end=MAX_MESSAGE_LENGTH)
			self.send_message(
				chat_id, text[:i_max],
				parse_mode=parse_mode or self.default_parse_mode,
				container=container, is_group=is_group,
				reply_markup=None, **kwargs
			)
			text = text[i_max + 1:]

		message_promise = Promise(
			super().send_message,
			(chat_id, text), dict(
				parse_mode=parse_mode or self.default_parse_mode,
				reply_markup=reply_markup, **kwargs
			)
		)
		if container is not None:
			container.append(message_promise)
		self._msg_queue(message_promise, is_group)

	def delete_message(self, *args, **kwargs):
		"""Deleting message (after resolving if it is a Promise)."""
		if not args:
			chat_id, message_id = kwargs.pop('chat_id'), kwargs.pop('message_id')
		elif len(args) == 1:
			if not isinstance(args[0], Promise):
				raise TypeError()
			if not (message := self.check_promise_result(args[0])):
				return
			chat_id, message_id = message.chat_id, message.message_id
		else:
			chat_id, message_id = args[0], args[1]

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
		if self.debug_mode:
			self._request = self._request.saved_handler
			logger.info('Debug mode turned off')
		else:
			self._request = TelegramRequestWrapper(self._request)
			logger.warning('Debug mode turned on')
		self.debug_mode = not self.debug_mode
