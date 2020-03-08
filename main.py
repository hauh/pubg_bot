import sys
from logging import getLogger

from telegram import ParseMode
from telegram.ext import Defaults, Updater

import config
import database
import texts
import buttons
import menu
import jobs

import admin
import matches
import profile

########################

logger = getLogger('bot')


def mainMenu(update, context, menu):
	user_id = int(update.effective_user.id)
	user = database.getUser(user_id)
	if not user or user['username'] != update.effective_user.username:
		database.saveUser(user_id, update.effective_user.username)
		user = database.getUser(user_id)
	context.user_data.update(user)
	admin_button = 0 if user['admin'] or user_id in config.admin_id else 1
	return (menu['msg'], menu['buttons'][admin_button:])


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


def updateMenuWithCallbacks():
	texts.menu['callback'] = mainMenu

	admin_menu = texts.menu['next']['admin']
	admin_menu['callback'] = admin.main
	admin_menu['next']['manage_admins']['next']['add_admin']['callback'] =\
		admin.addAdmin
	admin_menu['next']['manage_admins']['next']['del_admin']['callback'] =\
		admin.delAdmin

	matches_menu = texts.menu['next']['matches']
	matches_menu['callback'] = matches.main
	matches_menu['next']['slot_']['callback'] = matches.pickSlot
	for setting in matches_menu['next']['slot_']['next'].keys():
		setting_menu = matches_menu['next']['slot_']['next'][setting]['next']
		for setting_choice in setting_menu.values():
			setting_choice['callback'] = matches.getSlotSetting

	profile_menu = texts.menu['next']['profile']
	profile_menu['callback'] = profile.main
	profile_menu['next']['balance_history']['callback'] = profile.balanceHistory
	for update_option in profile_menu['next'].values():
		update_option['callback'] = profile.updateProfile


def main():
	try:
		database.prepareDB()
	except Exception:
		logger.critical("Database required!")
		sys.exit(-1)

	buttons.updateMenuWithButtons()
	updateMenuWithCallbacks()

	updater = Updater(
		token=config.bot_token,
		use_context=True,
		defaults=Defaults(parse_mode=ParseMode.MARKDOWN)
	)

	jobs.scheduleJobs(updater.job_queue)

	updater.dispatcher.add_handler(menu.MenuHandler(texts.menu))
	updater.dispatcher.add_error_handler(error)

	logger.info("Bot started")

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
