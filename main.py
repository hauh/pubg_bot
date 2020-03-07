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
	chat_id = int(update.effective_chat.id)
	username = update.effective_user.username
	user = database.getUser(user_id)
	if not user or user['chat_id'] != chat_id or user['username'] != username:
		database.saveUser(user_id, chat_id, username)
		user = database.getUser(user_id)
	context.user_data.update(user)
	message = texts.menu['msg']
	if 'awaiting_payment' in context.user_data:
		message += texts.game_awaits_payment
	if 'paid_game' in context.user_data:
		message += texts.game_starts_soon
	admin_button = 0 if user_id in config.admin_id else 1
	confirm_match_button = None if 'awaiting_payment' in context.user_data else -1
	return (message, texts.menu['buttons'][admin_button:confirm_match_button])


def payForGame(update, context):
	game = context.user_data.get('awaiting_payment', None)
	user_id = int(update.effective_user.id)

	if not game or user_id in game.paying_users:
		return mainMenu(update, context)

	validated_input = context.chat_data.pop('validated_input', None)
	if validated_input:
		answer = profile.withdrawFunds(user_id, context.user_data, new_value)
		update.callback_query.answer(answer, show_alert=True)
		if answer == texts.funds_withdrawn:
			game.paid(user_id)
			context.user_data['paid_game'] = context.user_data.pop('awaiting_payment')
		return mainMenu(update, context)

	confirm_button = []
	message = texts.confirmation_menu['msg'].format(
		game=str(game),
		balance=context.user_data['balance'],
		bet=game.settings['bet']
	)
	if context.user_data['balance'] < int(game.settings['bet']):
		message += texts.too_expensive_match
	else:
		confirm_button = [buttons.createButtons(
			texts.confirmation_menu, f'confirm_{game.slot_id}'
		)]
	return (
		message,
		[confirm_button] + texts.menu['next']['pay_for_game']['buttons']
	)


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


main_callbacks = {
	r'^main$'			: mainMenu,
	r'^pay_for_game$'	: payForGame,
}


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
			main_callbacks,
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
