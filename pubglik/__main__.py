"""Running bot."""

import sys
from logging import getLogger
from sqlite3 import DatabaseError

from telegram.ext import Updater
from telegram.ext.messagequeue import MessageQueue
from telegram.utils.request import Request

from . import config, database, games
from .callbacks import conversation_callbacks
from .core import Bot, PrivateConversationHandler
from .error import error
from .interface import answers, buttons, messages, optional_buttons
from .menutree import menu_tree

####################################

logger = getLogger('main')

updater = Updater(
	bot=Bot(
		config.bot_token,
		admin_chat=config.admin_chat,
		msg_queue=MessageQueue(
			all_burst_limit=29,
			all_time_limit_ms=1017,
			autostart=False
		),
		request=Request(
			con_pool_size=10,
			proxy_url=config.proxy if config.proxy else None
		)
	),
)


def main():
	try:
		database.prepare_DB()
	except DatabaseError:
		sys.exit(-1)

	dispatcher = updater.dispatcher

	dispatcher.add_handler(PrivateConversationHandler(
		menu_tree,
		menu_data={
			'callbacks': conversation_callbacks,
			'texts': messages,
			'buttons': buttons,
			'optional_buttons': optional_buttons,
			'answers': answers
		}
	))
	dispatcher.add_error_handler(error)

	updater.job_queue.set_dispatcher(dispatcher)
	updater.job_queue.run_once(games.restore_state, 0)
	updater.job_queue.run_repeating(games.check_slots_and_games, 300, first=60)

	updater.bot.msg_queue.start()
	updater.start_polling()
	logger.info("Bot started!")

	updater.idle()
	updater.bot.msg_queue.stop()
	logger.info('Bye!')


if __name__ == '__main__':
	main()
