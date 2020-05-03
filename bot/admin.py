'''Admin menu'''

import re

from telegram import ChatAction
from telegram.error import TelegramError, Unauthorized

import texts
import database
import excel
import utility

##############################

admin_menu = texts.menu['next']['admin']
manage_admins_menu = admin_menu['next']['manage_admins']
manage_matches_menu = admin_menu['next']['manage_matches']
set_winners_menu = manage_matches_menu['next']['set_winners_']


def with_admin_rights(admin_func):
	def check_rights(update, context, *menu):
		if not context.user_data.get('admin'):
			return (texts.menu['msg'],)
		return admin_func(update, context, *menu)
	return check_rights


@with_admin_rights
def admin_main(update, context, menu=admin_menu):
	return (menu['msg'],)


@with_admin_rights
def add_admin(update, context, menu):
	if admin_id := context.user_data.pop('validated_input', None):
		return switch_admin(update, context, menu, int(admin_id), True)

	if user_input := context.user_data.pop('user_input', None):
		if not (user := database.get_user(username=user_input)):
			return (menu['answers']['not_found'],)
		return (
			menu['answers']['found'].format(user['username']),
			utility.confirm_button(user['id'])
		)

	return (menu['msg'],)


@with_admin_rights
def revoke_admin(update, context, menu):
	if admin_id := context.user_data.pop('validated_input', None):
		return switch_admin(update, context, menu, int(admin_id), False)

	admins_buttons = [
		utility.confirm_button(admin['id'], f"@{admin['username']}")
		for admin in database.get_user(admin=True, fetch_all=True)
	]
	return (menu['msg'], *admins_buttons)


def switch_admin(update, context, menu, admin_id, new_state):
	database.update_user(admin_id, admin=new_state)
	context.dispatcher.user_data[admin_id]['admin'] = new_state
	update.callback_query.answer(menu['answers']['success'], show_alert=True)
	del context.user_data['history'][-2:]
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
	return (menu['msg'], *games_buttons)


def with_game_to_manage(manage_game_func):
	def find_game(update, context, *menu):
		current_game_id = int(context.user_data['history'][-1].split('_')[-1])
		for game in context.bot_data.get('games', []):
			if game.slot_id == current_game_id and not game.is_finished:
				return manage_game_func(update, context, game, *menu)
		return manage_matches(update, context)
	return find_game


@with_admin_rights
@with_game_to_manage
def set_room(update, context, game, menu):
	# if room id and pass confirmed set it and return back
	if id_and_pass := context.user_data.pop('validated_input', None):
		game.update_room(*id_and_pass.split(','))
		update.callback_query.answer(menu['answers']['success'], show_alert=True)
		del context.user_data['history'][-1]
		return manage_matches(update, context)

	# if no input ask for it
	if not (id_and_pass := context.user_data.pop('user_input', None)):
		return (menu['msg'].format(str(game), game.pubg_id, game.room_pass),)

	# input should be in 'pubg_id,pass' format
	try:
		pubg_id, room_pass = re.sub(r'\s', '', id_and_pass).split(',')
		pubg_id = int(pubg_id)
	except ValueError:
		return (menu['answers']['invalid_format'],)

	return (
		menu['answers']['confirm'].format(pubg_id, room_pass),
		utility.confirm_button(f'{pubg_id},{room_pass}')
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
			confirm_button, generate_table_button
		)

	update.effective_chat.send_action(ChatAction.TYPING)

	# if winners are set and confirmed mark game as finished for job worker
	if context.user_data.pop('validated_input', None) and game.winners_are_set:
		game.is_finished = True
		update.callback_query.answer(menu['answers']['success'], show_alert=True)
		del context.user_data['history'][-1]
		return manage_matches(update, context)

	generate_table_button = utility.button(
		f'generate_table_{game.slot_id}', menu['btn_template'])

	# if no file was uploaded ask for winners table
	if not (winners_file := context.user_data.pop('user_input', None)):
		return (menu['msg'], generate_table_button)

	# trying to load xlsx file
	if not (results := excel.read_table(winners_file.get_file())):
		return done('bad_file')

	game.reset_results()
	# reading file for places
	if possible_places := game.places_to_reward():
		for row, user_id, place in excel.get_winners(results):
			if place not in possible_places:
				return done('invalid_value', row)
			if not (player := game.players.get(user_id)):
				return done('unknown_player', row)
			player['place'] = place
			possible_places.remove(place)
		if possible_places:
			return done('not_enough')

	# reading file for kills
	if game.prize_structure['kills']:
		possible_kills = range(game.players_count)
		for row, user_id, kills in excel.get_killers(results):
			if kills not in possible_kills:
				return done('invalid_value', row)
			if not (player := game.players.get(user_id)):
				return done('unknown_player', row)
			player['kills'] = kills
		if game.total_kills != possible_kills[-1]:
			return done('wrong_kills', possible_kills[-1])

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
	del context.user_data['history'][-1]
	return set_winners(update, context)


@with_admin_rights
def mailing(update, context, menu):
	def spam(context):
		try:
			context.bot.send_message(*context.job.context)
		except Unauthorized:
			database.update_user(context.job.context[0], banned=True)
		except TelegramError:
			pass

	# if confirmed start spam
	if context.user_data.pop('validated_input', None):
		users = database.get_user(admin=False, banned=False, fetch_all=True)
		spam_message = context.bot_data.pop('spam_message')
		for delay, user in enumerate(users):
			context.job_queue.run_once(
				spam, delay * 0.1, context=(user['id'], spam_message))
		update.callback_query.answer(menu['answers']['success'])
		del context.user_data['history'][-1]
		return admin_main(update, context)

	# if got message ask to confirm
	if user_input := context.user_data.pop('user_input', None):
		context.bot_data['spam_message'] = user_input
		return (
			menu['answers']['success'].format(user_input),
			utility.confirm_button('spam')
		)

	return (menu['msg'],)


##############################

def add_callbacks():
	admin_menu['callback'] = admin_main
	admin_menu['next']['mailing']['callback'] = mailing

	manage_admins_menu['next']['add_admin']['callback'] = add_admin
	manage_admins_menu['next']['del_admin']['callback'] = revoke_admin

	manage_matches_menu['callback'] = manage_matches
	manage_matches_menu['next']['set_room_']['callback'] = set_room

	set_winners_menu['callback'] = set_winners
	set_winners_menu['next']['generate_table_']['callback'] = generate_table
