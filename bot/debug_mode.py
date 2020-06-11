'''Monkey patching bot instance to append tech info to messages'''

from types import MethodType

##############################


def debug_send_message(self, chat_id, text, **kwargs):
	text = f"*chat_id*: {chat_id}\n*kwargs*:\n{kwargs}\n*text*:\n{text}"
	return self.original_send_message(chat_id, text, **kwargs)


def debug_answer_callback_query(self, cb_query_id, text=None, **kwargs):
	text = f"*cb_query_id*: {cb_query_id}\n*kwargs*:\n{kwargs}\n*text*:\n{text}"
	return self.original_send_message(cb_query_id, text)


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
