import sys
from logging import getLogger

from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Defaults, Updater, Filters, CallbackQueryHandler

import config
import database
import texts
import jobs
from menu_handler import MenuHandler

import admin
import matches
import profile

########################

logger = getLogger('bot')


def start(update, context, menu):
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
		context.user_data.get('history'),
		type(context.error).__name__,
		context.error
	))
	if update.callback_query and update.callback_query.id != 0:
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
	texts.menu['callback'] = start

	admin_menu = texts.menu['next']['admin']
	admin_menu['callback'] = admin.mainAdmin
	manage_admins = admin_menu['next']['manage_admins']
	manage_admins['next']['add_admin']['callback'] = admin.addAdmin
	manage_admins['next']['del_admin']['callback'] = admin.delAdmin
	manage_matches = admin_menu['next']['manage_matches']
	manage_matches['callback'] = admin.manageMatches
	manage_matches['next']['set_game_id_']['callback'] = admin.setGameID
	manage_matches['next']['set_winners_']['callback'] = admin.setWinners
	manage_matches['next']['set_winners_']['next']['place_']['callback'] =\
		admin.setEachWinner

	matches_menu = texts.menu['next']['matches']
	matches_menu['callback'] = matches.mainMatches
	matches_menu['next']['slot_']['callback'] = matches.slotMenu
	for setting in matches_menu['next']['slot_']['next'].keys():
		setting_menu = matches_menu['next']['slot_']['next'][setting]['next']
		for setting_choice in setting_menu.values():
			setting_choice['callback'] = matches.getSlotSetting

	profile_menu = texts.menu['next']['profile']
	profile_menu['callback'] = profile.mainProfile
	profile_menu['next']['set_pubg_id']['callback'] = profile.setPubgID
	profile_menu['next']['set_pubg_username']['callback'] =\
		profile.setPubgUsername
	profile_menu['next']['add_funds']['callback'] = profile.addFunds
	profile_menu['next']['withdraw_funds']['callback'] = profile.withdrawFunds
	profile_menu['next']['balance_history']['callback'] = profile.balanceHistory


def gotoAdmin(update, context):
	text, buttons = admin.manageMatches(
		update, context, texts.menu['next']['admin']['next']['manage_matches'])
	if text:
		old_messages = context.user_data.setdefault('old_messages', [])
		MenuHandler.cleanChat(old_messages)
		old_messages.append(
			update.effective_user.send_message(
				text, reply_markup=InlineKeyboardMarkup(buttons))
		)


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
	updater.dispatcher.add_handler(
		CallbackQueryHandler(gotoAdmin, pattern='manage_matches'))
	updater.dispatcher.add_error_handler(error)

	logger.info("Bot started")

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
