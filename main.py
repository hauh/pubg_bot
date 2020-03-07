import sys
from logging import getLogger

from telegram import ParseMode
from telegram.ext import Defaults, Updater

import config
import database
import texts
import buttons
import menu
import matches
import profile
import admin
import jobs

########################

logger = getLogger('bot')


def mainMenu(update, context):
	user_id = int(update.effective_user.id)
	user = database.getUser(user_id)
	if not user or user['username'] != update.effective_user.username:
		database.saveUser(user_id, update.effective_user.username)
		user = database.getUser(user_id)
	context.user_data.update(user)
	admin_button = 0 if user['admin'] or user_id in config.admin_id else 1
	return (texts.menu['msg'], texts.menu['buttons'][admin_button:])


def error(update, context):
	logger.error("History: {}, Error: {}, Argument: {}".format(
		context.chat_data.get('history'),
		type(context.error).__name__,
		context.error
	))
	if update.callback_query:
		update.callback_query.answer(texts.error, show_alert=True)
	else:
		context.chat_data.setdefault('old_messages', []).append(
			update.effective_chat.send_message(texts.error))


def main():
	try:
		database.prepareDB()
	except Exception:
		logger.critical("Database required!")
		sys.exit(-1)

	buttons.updateMenuWithButtons()

	updater = Updater(
		token=config.bot_token,
		use_context=True,
		defaults=Defaults(parse_mode=ParseMode.MARKDOWN)
	)

	jobs.scheduleJobs(updater.job_queue)

	updater.dispatcher.add_handler(menu.MenuHandler(
		texts.menu,
		[
			{r'^main$': mainMenu},
			admin.callbacks,
			matches.callbacks,
			profile.callbacks,
		])
	)
	updater.dispatcher.add_error_handler(error)

	logger.info("Bot started")

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
