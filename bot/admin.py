import re
from logging import getLogger

from telegram import ChatAction

import texts
import database
import excel
import utility

##############################

logger = getLogger(__name__)
admin_menu = texts.menu['next']['admin']
manage_admins_menu = admin_menu['next']['manage_admins']
manage_matches_menu = admin_menu['next']['manage_matches']
set_winners_menu = manage_matches_menu['next']['set_winners_']


def with_admin_rights(admin_func):
	def check_rights(update, context, *menu):
		if not context.user_data.get('admin'):
			return (texts.menu['msg'], texts.menu['buttons'][1:])
		return admin_func(update, context, *menu)
	return check_rights


@with_admin_rights
def admin_main(update, context, menu=admin_menu):
	return (menu['msg'], menu['buttons'])


@with_admin_rights
def add_admin(update, context, menu):
	if admin_id := context.user_data.pop('validated_input', None):
		return switch_admin(update, context, menu, int(admin_id), True)

	user_input = context.user_data.pop('user_input', None)
	if user := database.get_user(username=user_input):
		message = menu['answers']['found'].format(user['username'])
		confirm_button = utility.create_button(user['id'])
	else:
		message = menu['answers']['not_found']
		confirm_button = []
	return (message, [confirm_button] + menu['buttons'])


@with_admin_rights
def revoke_admin(update, context, menu):
	if admin_id := context.user_data.pop('validated_input', None):
		return switch_admin(update, context, menu, int(admin_id), False)

	admins_buttons = []
	admins_list = ""
	for admin in database.get_user(admin=True):
		admins_buttons.append(utility.create_button(
			f"@{admin['username']}", f"confirm_{admin['id']}"))
		admins_list += f"@{admin['username']}\n"
	return (menu['msg'].format(admins_list), admins_buttons + menu['buttons'])


def switch_admin(update, context, menu, admin_id, new_state):
	database.update_user(admin_id, admin=new_state)
	context.dispatcher.user_data[admin_id]['admin'] = new_state
	update.callback_query.answer(menu['answers']['success'], show_alert=True)
	del context.user_data['history'][-2:]
	return admin_main(update, context)


@with_admin_rights
def manage_matches(update, context, menu=manage_matches_menu):
	games = context.bot_data.get('games', [])
	games_buttons = []
	for game in sorted(games, key=lambda game: game.time):
		if game.is_running:
			button_text = menu['btn_template'].format(
				status='🏆', room_id=game.pubg_id, game=str(game))
			button_data = f"set_winners_{game.slot_id}"
		else:
			button_text = menu['btn_template'].format(
				status='🕑', room_id=game.pubg_id, game=str(game))
			button_data = f"set_room_id_{game.slot_id}"
		games_buttons.append(utility.create_button(button_text, button_data))
	return (menu['msg'], games_buttons + menu['buttons'])


def with_game_to_manage(manage_game_func):
	def find_game(update, context, *menu):
		current_game_id = int(context.user_data['history'][-1].split('_')[-1])
		for game in context.bot_data.get('games', []):
			if game.slot_id == current_game_id:
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

	message = menu['msg'].format(str(game), game.pubg_id, game.room_pass)

	# if no input ask for it
	if not (id_and_pass := context.user_data.pop('user_input', None)):
		return (message, menu['buttons'])

	# input should be in 'pubg_id,pass' format
	try:
		pubg_id, room_pass = re.sub(r'\s', '', id_and_pass).split(',')
		pubg_id = int(pubg_id)
	except ValueError:
		answer = menu['answers']['invalid_format']
		confirm_button = []
	else:
		answer = menu['answers']['confirm'].format(pubg_id, room_pass)
		confirm_button = utility.confirm_button(f'{pubg_id},{room_pass}')

	return (message + answer, [confirm_button] + menu['buttons'])


@with_admin_rights
@with_game_to_manage
def set_winners(update, context, game, menu=set_winners_menu):
	def done(answer, *format_args, confirm=False):
		if confirm:
			confirm_button = utility.confirm_button('winners')
		else:
			confirm_button = []
			game.reset_winners()
		return (
			menu['answers'][answer].format(*format_args),
			[confirm_button] + [generate_table_button] + menu['buttons']
		)

	update.effective_chat.send_action(ChatAction.TYPING)

	# reward players if winners are set and confirmed
	if context.user_data.pop('validated_input', None) and game.winners_are_set:
		for player_id in game.players:
			player_data = context.dispatcher.user_data.get(player_id)
			try:
				player_data.pop('game_message').delete()
			except Exception:
				pass
		winners, total_payouts = game.reward()
		for winner_id, victory_message, prize in winners:
			winner_data = context.dispatcher.user_data.get(winner_id)
			winner_data['balance'] = database.change_balance(
				winner_id, prize, 'prize', game.slot_id)
			winner_data['game_message'] = context.bot.send_message(
				winner_id,
				texts.victory.format(
					game=str(game), victory_message=victory_message, prize=prize)
			)
		logger.info(f"Game ended, winners are, payout: {total_payouts}")
		utility.message_admins(
			context.bot, 'prizes',
			game=str(game), pubg_id=game.pubg_id,
			total_bets=game.prize_fund, prizes=total_payouts
		)
		context.bot_data.get('running_games', set()).discard(game)

		update.callback_query.answer(menu['input']['msg_success'], show_alert=True)
		del context.user_data['history'][-1]
		distribute_prizes(context, game)
		return manage_matches(update, context)

	generate_table_button = utility.create_button(
		menu['btn_template'], f'generate_table_{game.slot_id}')

	# if no file was uploaded ask for winners table
	if not (file_upload := update.effective_message.document):
		return (menu['msg'], [generate_table_button] + menu['buttons'])

	# trying to load xlsx file
	if not (results := excel.read_table(file_upload.get_file())):
		return done('bad_file')

	# reading file for places
	if game.game_type != 'kills':
		for row, user_id, place in excel.get_winners(results):
			if user_id not in game.players:
				return done('unknown_player', row)
			if place not in game.winning_places:
				return done('invalid_value', row)
			if user_id in game.winners.values():
				return done('duplicate_player', row)
			if game.winners[place]:
				return done('duplicate_place', row)
			game.winners[place] = user_id
		if not all(game.winners.values()):
			return done('not_enough')

	# reading file for kills
	if game.game_type != 'survival':
		possible_kills = range(1, game.players_count)
		for row, user_id, kills in excel.get_killers(results):
			if user_id not in game.players:
				return done('unknown_player', row)
			if kills not in possible_kills:
				return done('invalid_value', row)
			if user_id in game.killers:
				return done('duplicate_player', row)
			game.killers[user_id] = kills
		if game.total_kills != possible_kills[-1]:
			return done('wrong_kills', possible_kills[-1])

	if not game.winners_are_set:
		return done('missing_something')

	return done('confirm', confirm=True)


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
		user_id, spam_message = context.job.context
		try:
			context.bot.send_message(user_id, spam_message)
		except Exception as err:
			logger.error('Sending message to {} failed because: {}, {}'.format(
				user_id, type(err).__name__, err.args))

	if confirm_spam := context.user_data.pop('validated_input', None):
		users = database.get_user(admin=False)
		for delay, user in enumerate(users):
			context.job_queue.run_once(
				spam, delay * 0.1,
				context=(user['id'], context.bot_data.pop('spam_message'))
			)
		update.callback_query.answer(menu['input']['msg_success'])
		return admin_main(update, context)

	if user_input := context.user_data.pop('user_input', None):
		context.bot_data['spam_message'] = user_input
		return (
			menu['input']['msg_valid'].format(user_input),
			[utility.confirm_button('spam')] + menu['buttons']
		)

	return (menu['msg'], menu['buttons'])


##############################

admin_menu['callback'] = admin_main
admin_menu['next']['mailing']['callback'] = mailing

manage_admins_menu['next']['add_admin']['callback'] = add_admin
manage_admins_menu['next']['del_admin']['callback'] = revoke_admin

manage_matches_menu['callback'] = manage_matches
manage_matches_menu['next']['set_room_']['callback'] = set_room

set_winners_menu['callback'] = set_winners
set_winners_menu['next']['generate_table_']['callback'] = generate_table
