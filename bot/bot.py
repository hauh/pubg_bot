import sys
from logging import getLogger

from telegram import ParseMode, InlineKeyboardButton
from telegram.ext import Defaults, Updater

import config
import database
import texts
import jobs
from menu_handler import MenuHandler

import main_menu
import admin
import matches
import profile

########################

logger = getLogger('bot')


def error(update, context):
	logger.error("History: {}, Error: {}, Argument: {}".format(
		context.user_data.get('history'),
		type(context.error).__name__,
		context.error
	))
	if update.callback_query:
		update.callback_query.answer(texts.error, show_alert=True)
	else:
		context.user_data.setdefault('old_messages', []).append(
			update.effective_chat.send_message(texts.error))


def updateMenuWithButtons():
	def generateButtons(menu, depth=0):
		buttons = []
		if 'next' in menu:
			for button_key, button_data in menu['next'].items():
				if 'btn' in button_data:
					buttons.append([InlineKeyboardButton(
						button_data['btn'], callback_data=button_key)])
				generateButtons(button_data, depth + 1)
		if depth > 1:
			buttons.append(back_button + main_button)
		elif depth:
			buttons.append(back_button)
		menu['buttons'] = buttons

	back_button = [InlineKeyboardButton(texts.back, callback_data='back')]
	main_button = [InlineKeyboardButton(texts.main, callback_data='main')]
	generateButtons(texts.menu)
	texts.menu['buttons'][5][0].url = config.battle_chat


def updateMenuWithCallbacks():
	texts.menu['callback'] = main_menu.start

	admin_menu = texts.menu['next']['admin']
	admin_menu['callback'] = admin.mainAdmin
	admin_menu['next']['manage_admins']['next']['add_admin']['callback'] =\
		admin.addAdmin
	admin_menu['next']['manage_admins']['next']['del_admin']['callback'] =\
		admin.delAdmin

	matches_menu = texts.menu['next']['matches']
	matches_menu['callback'] = matches.mainMatches
	matches_menu['next']['slot_']['callback'] = matches.slotMenu
	for setting in matches_menu['next']['slot_']['next'].keys():
		setting_menu = matches_menu['next']['slot_']['next'][setting]['next']
		for setting_choice in setting_menu.values():
			setting_choice['callback'] = matches.getSlotSetting

	profile_menu = texts.menu['next']['profile']
	profile_menu['callback'] = profile.mainProfile
	for update_option in profile_menu['next'].values():
		update_option['callback'] = profile.updateProfile
	profile_menu['next']['balance_history']['callback'] = profile.balanceHistory


def main():
	try:
		database.prepareDB()
	except Exception:
		logger.critical("Database required!")
		sys.exit(-1)

	updateMenuWithButtons()
	updateMenuWithCallbacks()

	updater = Updater(
		token=config.bot_token,
		use_context=True,
		defaults=Defaults(parse_mode=ParseMode.MARKDOWN)
	)

	jobs.scheduleJobs(updater.job_queue)

	updater.dispatcher.add_handler(MenuHandler(texts.menu))
	updater.dispatcher.add_error_handler(error)

	logger.info("Bot started")

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
