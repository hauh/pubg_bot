"""Main, bot starts here"""

from logging import getLogger

from telegram import InlineKeyboardMarkup
from telegram.ext import JobQueue

from pubglik import config, database
from . import texts, games
from .core import MenuHandler, utility
from .menus import admin, tournaments, cabinet

########################

logger = getLogger('bot')


def start(update, context, menu):
	user_id = int(update.effective_user.id)
	username = update.effective_user.username
	if not (user := database.get_user(user_id)):
		user = database.save_user(user_id, username)
		user['balance'] = 0
		user['games_played'] = 0
	if user['banned']:
		return (texts.banned, None)
	if user['username'] != username:
		database.update_user(user_id, username=username)
		user['username'] = username
	if not user['admin'] and user_id in config.admin_id:
		database.update_user(user_id, admin=True)
		user['admin'] = True
	context.user_data.update(user)
	if user['pubg_username']:
		msg = menu['msg_registered'].format(
			user['pubg_username'], user['balance'], user['games_played'])
	else:
		msg = menu['msg']
	if user['admin']:
		return (msg, [menu['extra_buttons']['admin']] + menu['buttons'])
	return (msg, menu['buttons'])


def error(update, context):
	err = (type(context.error), context.error, None)

	if not update or not context.user_data:
		logger.error("Bot broke down!", exc_info=err)
		return

	if update.callback_query:
		update.callback_query.answer(texts.error, show_alert=True)
		failed_message = update.callback_query.data
	else:
		failed_message = update.message.text
	conversation = context.user_data.get('conversation')
	logger.error(
		"User %s broke down bot in menu %s, failed message: %s",
		update.effective_user.id, str(conversation),
		failed_message, exc_info=err
	)
	main_menu_text, buttons = start(update, context, texts.menu)
	update.effective_chat.send_message(
		main_menu_text,
		reply_markup=InlineKeyboardMarkup(buttons) if any(buttons) else None,
		container=conversation.messages if conversation else None
	)


def setup(dispatcher):
	def add_buttons(menu, depth=0):
		buttons = []
		for key, next_menu in menu.get('next', {}).items():
			if 'btn' in next_menu:
				buttons.append(utility.button(key, next_menu['btn']))
			add_buttons(next_menu, depth + 1)
		if depth:
			buttons.append(back_button + (main_button if depth > 1 else []))
		menu['buttons'] = buttons
		for key, text in menu.get('extra_buttons', {}).items():
			menu['extra_buttons'][key] = utility.button(key, text)

	# adding buttons to menu
	back_button = utility.button('_back_', texts.back)
	main_button = utility.button('_main_', texts.main)
	add_buttons(texts.menu)
	texts.menu['buttons'][4][0].url = config.battle_chat

	# adding callbacks to menu
	texts.menu['callback'] = start
	admin.add_callbacks()
	tournaments.add_callbacks()
	cabinet.add_callbacks()

	dispatcher.add_handler(MenuHandler(texts.menu))
	dispatcher.add_error_handler(error)

	job_queue = JobQueue()
	job_queue.set_dispatcher(dispatcher)
	dispatcher.job_queue = job_queue
	job_queue.run_once(games.restore_state, 0)
	job_queue.run_repeating(games.check_slots_and_games, 300, first=60)
	job_queue.start()
