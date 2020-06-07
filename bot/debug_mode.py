'''Monkey patching bot instance to send all messages to debug chat'''

from types import MethodType

import config

##############################


def debug_send_message(self, chat_id, text, **kwargs):
	if chat_id not in config.admin_id:
		text = f"Message for {chat_id}:\n{text}"
		chat_id = config.debug_chat
	return self.original_send_message(chat_id, text, **kwargs)


def debug_answer_callback_query(self, callback_query_id, text=None, **kwargs):
	text = f"Answer to callback query id {callback_query_id}:\n{text}"
	return self.original_send_message(config.debug_chat, text)


def turn_on(bot):
	setattr(bot, 'original_send_message', bot.send_message)
	setattr(bot, 'original_answer_callback_query', bot.answer_callback_query)
	bot.send_message = MethodType(debug_send_message, bot)
	bot.answer_callback_query = MethodType(debug_answer_callback_query, bot)
	bot.sendMessage = bot.send_message
	bot.answerCallbackQuery = bot.answer_callback_query


def turn_off(bot):
	bot.send_message = bot.original_send_message
	bot.answer_callback_query = bot.original_answer_callback_query
	bot.sendMessage = bot.send_message
	bot.answerCallbackQuery = bot.answer_callback_query
	delattr(bot, 'original_send_message')
	delattr(bot, 'original_answer_callback_query')
