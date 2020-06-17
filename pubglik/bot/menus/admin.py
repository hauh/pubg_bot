"""Admin menu"""

import re

from telegram import ChatAction

from pubglik import database
from pubglik.bot import texts
from pubglik.bot.core import debug_mode, utility
from pubglik.bot.misc import excel

##############################

admin_menu = texts.menu['next']['admin']
manage_matches_menu = admin_menu['next']['manage_matches']
set_winners_menu = manage_matches_menu['next']['set_winners_']
manage_admins_menu = admin_menu['next']['manage_admins']
manage_users_menu = admin_menu['next']['manage_users']
bot_settings_menu = admin_menu['next']['bot_settings']


def with_admin_rights(admin_func):
	def check_rights(update, context, *menu):
		if not context.user_data.get('admin'):
			raise PermissionError(
				f"User id: {update.effective_user.id}, "
				f"Telegram username: {context.user_data.get('username')}"
			)
		return admin_func(update, context, *menu)
	return check_rights


@with_admin_rights
def admin_main(update, context, menu=admin_menu):
	return (menu['msg'], menu['buttons'])


@with_admin_rights
def add_admin(update, context, menu):
	if admin_id := context.user_data.pop('validated_input', None):
		return switch_admin(update, context, menu, int(admin_id), True)

	if user_input := context.user_data.pop('user_input', None):
		if not (user := database.find_user(username=user_input)):
			return (menu['answers']['not_found'], menu['buttons'])
		return (
			menu['answers']['found'].format(user['username']),
			[utility.confirm_button(user['id'])] + menu['buttons']
		)

	return (menu['msg'], menu['buttons'])


@with_admin_rights
def revoke_admin(update, context, menu):
	if admin_id := context.user_data.pop('validated_input', None):
		return switch_admin(update, context, menu, int(admin_id), False)

	admins_buttons = [
		utility.confirm_button(admin['id'], f"@{admin['username']}")
		for admin in database.find_user(admin=True, fetch_all=True)
	]
	return (menu['msg'], admins_buttons + menu['buttons'])


def switch_admin(update, context, menu, admin_id, new_state):
	database.update_user(admin_id, admin=new_state)
	context.dispatcher.user_data[admin_id]['admin'] = new_state
	update.callback_query.answer(menu['answers']['success'], show_alert=True)
	context.user_data['conversation'].back(level=2)
	return admin_main(update, context)


@with_admin_rights
def manage_matches(update, context, menu=manage_matches_menu):
	games_buttons = []
	for game in context.bot_data.get('games', []):
		if not game.is_running:
			games_buttons.append(utility.button(
				f"set_room_id_{game.slot_id}",
				menu['btn_template'].format(
					status='🕑', room_id=game.pubg_id, game=str(game)),
			))
		elif not game.is_finished:
			games_buttons.append(utility.button(
				f"set_winners_{game.slot_id}",
				menu['btn_template'].format(
					status='🏆', room_id=game.pubg_id, game=str(game)),
			))
	return (menu['msg'], games_buttons + menu['buttons'])


def with_game_to_manage(manage_game_func):
	def find_game(update, context, *menu):
		game_button = context.user_data['conversation'].repeat()
		picked_game_id = int(game_button.split('_')[-1])
		for game in context.bot_data.get('games', []):
			if game.slot_id == picked_game_id and not game.is_finished:
				return manage_game_func(update, context, game, *menu)
		return manage_matches(update, context)
	return find_game


@with_admin_rights
@with_game_to_manage
def set_room(update, context, game, menu):
	# if room id and pass confirmed set it and return back
	if id_and_pass := context.user_data.pop('validated_input', None):
		game.run_game(*id_and_pass.split(','))
		update.callback_query.answer(menu['answers']['success'], show_alert=True)
		context.user_data['conversation'].back()
		return manage_matches(update, context)

	# if no input ask for it
	if not (id_and_pass := context.user_data.pop('user_input', None)):
		return (
			menu['msg'].format(str(game), game.pubg_id, game.room_pass),
			menu['buttons']
		)

	# input should be in 'pubg_id,pass' format
	try:
		pubg_id, room_pass = re.sub(r'\s', '', id_and_pass).split(',')
		pubg_id = int(pubg_id)
	except ValueError:
		return (menu['answers']['invalid_format'], menu['buttons'])

	return (
		menu['answers']['confirm'].format(pubg_id, room_pass),
		[utility.confirm_button(f'{pubg_id},{room_pass}')] + menu['buttons']
	)


@with_admin_rights
@with_game_to_manage
def set_winners(update, context, game, menu=set_winners_menu):
	def done(answer, *format_args, confirm=False):
		if confirm:
			confirm_button = utility.confirm_button('winners')
		else:
			confirm_button = []
			game.reset_results()
		return (
			menu['answers'][answer].format(*format_args),
			[confirm_button] + [generate_table_button] + menu['buttons']
		)

	update.effective_chat.send_action(ChatAction.TYPING)

	# if winners are set and confirmed mark game as finished for job worker
	if context.user_data.pop('validated_input', None) and game.winners_are_set:
		game.is_finished = True
		update.callback_query.answer(menu['answers']['success'], show_alert=True)
		context.user_data['conversation'].back()
		return manage_matches(update, context)

	generate_table_button = utility.button(
		f'generate_table_{game.slot_id}', menu['btn_template'])

	# if no file was uploaded ask for winners table
	if not (winners_file := context.user_data.pop('user_input', None)):
		return (menu['msg'], [generate_table_button] + menu['buttons'])

	# trying to load xlsx file
	if not (results := excel.read_table(winners_file.get_file())):
		return done('bad_file')

	game.reset_results()
	# reading file for places and kills
	try:
		if hasattr(game.game, 'places'):
			for row, user_id, place in excel.get_winners(results):
				game.game.set_player_place(user_id, place)
		if hasattr(game.game, 'kills'):
			for row, user_id, kills in excel.get_killers(results):
				game.game.set_player_kills(user_id, kills)
	except ValueError as err:
		return done(err.args[0], row)

	if not game.winners_are_set:
		return done('missing_something')

	total_payouts = game.distribute_prizes()
	return done('confirm', game.prize_fund, total_payouts, confirm=True)


@with_admin_rights
@with_game_to_manage
def generate_table(update, context, game, menu):
	update.effective_chat.send_action(ChatAction.TYPING)
	update.effective_chat.send_document(
		excel.create_table(database.get_players(game.slot_id)),
		filename=f'{game.pubg_id}.xlsx'
	)
	context.user_data['conversation'].back()
	return set_winners(update, context)


@with_admin_rights
def manage_users(update, context, menu):
	if not (user_input := context.user_data.pop('user_input', None)):
		return (menu['msg'], menu['buttons'])

	if user_input.startswith('@'):
		user = database.find_user(username=user_input[1:])
	else:
		try:
			user = database.find_user(pubg_id=int(user_input))
		except ValueError:
			user = None
	if not user:
		return (menu['answers']['user_not_found'], menu['buttons'])

	user['balance'] = database.get_balance(user['id'])
	context.dispatcher.user_data.setdefault(user['id'], {}).update(user)
	change_balance_button = utility.button(
		f"change_balance_{user['id']}",
		menu['btn_templates']['change_balance']
	)
	switch_ban_button = utility.button(
		f"switch_ban_{user['id']}",
		menu['btn_templates']['ban'] if not user['banned']
			else menu['btn_templates']['unban']
	)
	return (
		menu['answers']['user_found'].format(**user),
		[change_balance_button] + [switch_ban_button] + menu['buttons']
	)


@with_admin_rights
def change_user_balance(update, context, menu):
	user_id = int(update.callback_query.data.split('_')[-1])
	user_data = context.dispatcher.user_data.get(user_id)

	if amount := context.user_data.pop('validated_input', None):
		user_data['balance'] = database.change_balance(
			user_id, int(amount), 'by_admin', ext_id=update.effective_user.id)
		update.callback_query.answer(menu['answers']['success'])
		context.user_data['conversation'].back(level=2)
		return admin_main(update, context)

	if user_input := context.user_data.pop('user_input', None):
		try:
			amount = int(user_input)
		except ValueError:
			pass
		else:
			return (
				menu['msg'].format(**user_data)
					+ menu['answers']['confirm'].format(amount),
				[utility.confirm_button(amount)] + menu['buttons']
			)

	return (
		menu['msg'].format(**user_data) + menu['answers']['ask_for_input'],
		menu['buttons']
	)


@with_admin_rights
def switch_ban(update, context, menu):
	user_id = int(update.callback_query.data.split('_')[-1])
	user_data = context.dispatcher.user_data.get(user_id)
	user_data['banned'] = not user_data['banned']
	database.update_user(user_id, banned=user_data['banned'])
	if not user_data['banned']:
		update.callback_query.answer(menu['answers']['unbanned'])
	else:
		update.callback_query.answer(menu['answers']['banned'])
		if (user_conversation := user_data.pop('conversation', None)):
			user_conversation.clean_chat()
		for game in user_data.pop('picked_slots', []):
			game.leave(user_id)
	context.user_data['conversation'].back(level=2)
	return admin_main(update, context)


@with_admin_rights
def mailing(update, context, menu):
	# if confirmed start spam
	if context.user_data.pop('validated_input', None):
		spam_message = context.bot_data.pop('spam_message')
		for user in database.find_user(admin=False, banned=False, fetch_all=True):
			context.bot.send_message(user['id'], spam_message)
		update.callback_query.answer(menu['answers']['success'])
		context.user_data['conversation'].back()
		return admin_main(update, context)

	# if got message ask to confirm
	if user_input := context.user_data.pop('user_input', None):
		context.bot_data['spam_message'] = user_input
		return (
			menu['answers']['success'].format(user_input),
			[utility.confirm_button('spam')] + menu['buttons']
		)

	return (menu['msg'], menu['buttons'])


@with_admin_rights
def bot_settings(update, context, menu=bot_settings_menu):
	if context.bot_data['debug']:
		debug_btn = menu['extra_buttons']['debug_off']
	else:
		debug_btn = menu['extra_buttons']['debug_on']
	return (menu['msg'], [debug_btn] + menu['buttons'])


@with_admin_rights
def switch_debug(update, context, menu):
	if context.bot_data['debug']:
		debug_mode.turn_off(context.bot)
		update.callback_query.answer(menu['answers']['debug_off'])
	else:
		update.callback_query.answer(menu['answers']['debug_on'], show_alert=True)
		debug_mode.turn_on(context.bot)
	context.bot_data['debug'] = not context.bot_data['debug']
	context.user_data['conversation'].back()
	return bot_settings(update, context)


##############################

def add_callbacks():
	admin_menu['callback'] = admin_main
	admin_menu['next']['mailing']['callback'] = mailing

	manage_matches_menu['callback'] = manage_matches
	manage_matches_menu['next']['set_room_']['callback'] = set_room

	set_winners_menu['callback'] = set_winners
	set_winners_menu['next']['generate_table_']['callback'] = generate_table

	manage_admins_menu['next']['add_admin']['callback'] = add_admin
	manage_admins_menu['next']['del_admin']['callback'] = revoke_admin

	manage_users_menu['callback'] = manage_users
	manage_users_menu['next']['change_balance_']['callback'] = change_user_balance
	manage_users_menu['next']['switch_ban_']['callback'] = switch_ban

	bot_settings_menu['callback'] = bot_settings
	bot_settings_menu['next']['debug_']['callback'] = switch_debug
