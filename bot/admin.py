import re
from logging import getLogger

import texts
import database
import utility

##############################

logger = getLogger(__name__)
admin_menu = texts.menu['next']['admin']
manage_admins_menu = admin_menu['next']['manage_admins']
manage_matches_menu = admin_menu['next']['manage_matches']


def with_admin_rights(admin_func):
	def check_rights(update, context, *menu):
		if not context.user_data.get('admin'):
			return (None, None)
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
	pending_games = context.bot_data.get('pending_games', [])
	running_games = context.bot_data.get('running_games', [])

	buttons = []
	for slot in pending_games:
		buttons.append(utility.create_button(
			menu['next']['set_game_id_']['btn_template'].format(
				game=str(slot), pubg_id=slot.pubg_id, room_pass=slot.room_pass),
			f"set_game_id_{slot.slot_id}"
		))
	for slot in running_games:
		buttons.append(utility.create_button(
			menu['next']['set_winners_']['btn_template'].format(
				game=str(slot), pubg_id=slot.pubg_id, room_pass=slot.room_pass),
			f"set_winners_{slot.slot_id}"
		))
	return (
		menu['msg'].format(
			pending='\n'.join(str(game) for game in pending_games)
				if pending_games else menu['default'],
			running='\n'.join(str(game) for game in running_games)
				if running_games else menu['default']
		),
		buttons + menu['buttons']
	)


def with_existing_game(manage_match_func):
	def check_game(update, context, menu):
		where = context.user_data['history'][-1]
		if where.startswith('set_game_id'):
			games = context.bot_data.get('pending_games', {})
		elif where.startswith('set_winners') or where.startswith('set_killers'):
			games = context.bot_data.get('running_games', {})
		else:
			games = set()
		game_id = int(where.split('_')[-1])
		for game in games:
			if game.slot_id == game_id:
				return manage_match_func(update, context, menu, game)

		update.callback_query.answer(texts.error, show_alert=True)
		del context.user_data['history'][-1:]
		return manage_matches(update, context)
	return check_game


@with_admin_rights
@with_existing_game
def set_game_id(update, context, menu, game):
	if validated_input := context.user_data.pop('validated_input', None):
		game.update_room(*validated_input.split(','))
		answer = menu['input']['msg_success']
		update.callback_query.answer(answer, show_alert=True)
		del context.user_data['history'][-1:]
		return manage_matches(update, context)

	confirm_button = []
	if not (user_input := context.user_data.pop('user_input', None)):
		message = menu['msg'].format(
			game=str(game), pubg_id=game.pubg_id, room_pass=game.room_pass)
	else:
		try:
			pubg_id, room_pass = user_input.split(',')
		except ValueError:
			message = menu['input']['msg_error']
		else:
			confirm_button = utility.confirm_button(f'{pubg_id},{room_pass}')
			message = menu['input']['msg_valid'].format(
				game=str(game), pubg_id=pubg_id, room_pass=room_pass)
	return (message, [confirm_button] + menu['buttons'])


@with_admin_rights
@with_existing_game
def set_winners(update, context, menu, game):
	if all_winner_set := context.user_data.pop('validated_input', None):
		update.callback_query.answer(menu['input']['msg_success'], show_alert=True)
		del context.user_data['history'][-1]
		distribute_prizes(context, game)
		return manage_matches(update, context)

	games_buttons = []
	if game.winners_are_set:
		games_buttons.append(utility.confirm_button('winners'))
	winners = ""
	if game.game_type != 'kills':
		for place, winner in game.winners.items():
			winner_description = menu['next']['place_']['btn_template'].format(
				place=place, username=winner)
			games_buttons.append(utility.create_button(
				winner_description, f"place_{game.slot_id}_{place}"))
			winners += winner_description
	if game.game_type != 'survival':
		games_buttons.append(utility.create_button(
			menu['next']['set_killers_']['btn_template'],
			f"set_killers_{game.slot_id}"
		))
	return (
		menu['msg'].format(
			game=str(game),
			pubg_id=game.pubg_id,
			kills=game.total_kills,
			winners=winners
		),
		games_buttons + menu['buttons']
	)


@with_admin_rights
def set_each_winner(update, context, menu):
	game_cb_data = update.callback_query.data.lstrip('place_').split('_')
	game_id = int(game_cb_data[0])
	place = int(game_cb_data[1])
	if not (user_input := context.user_data.pop('user_input', None)):
		return (menu['msg'].format(place), menu['buttons'])

	running_games = context.bot_data.get('running_games', {})
	for game in running_games:
		if game.slot_id == game_id:
			if not (user := database.get_user(pubg_username=user_input)):
				try:
					user = database.get_user(pubg_id=int(user_input))
				except (TypeError, ValueError):
					pass
			if not user:
				game.winners[place] = texts.user_not_found
				return (menu['input']['msg_fail'], menu['buttons'])

			game.winners[place] = user['pubg_username']
			del context.user_data['history'][-1:]
			return set_winners(
				update, context,
				admin_menu['next']['manage_matches']['next']['set_winners_']
			)

	del context.user_data['history'][-1:]
	return manage_matches(update, context)


@with_admin_rights
@with_existing_game
def set_killers(update, context, menu, game):
	user_input = context.user_data.pop('user_input', None)
	error_message = None
	if user_input:
		if not re.match(r'^.+,[0-9][0-9]?$', user_input):
			error_message = menu['input']['msg_error']
		else:
			username, score = user_input.split(',')
			if not (user := database.get_user(pubg_username=username)):
				try:
					user = database.get_user(pubg_id=int(username))
				except (TypeError, ValueError):
					pass
			if not user:
				error_message = menu['input']['msg_fail']
			else:
				username = user['pubg_username']
				score = int(score)
				if username in game.killers.keys() and score == 0:
					del game.killers[username]
				elif game.total_kills + score > game.players_count - 1:
					error_message = menu['input']['msg_fail']
				else:
					game.killers[username] = score

	return (
		menu['msg'].format(
			kills=game.total_kills,
			players=game.players_count,
			killers="\n".join(
				[f'{killer} - {score}' for killer, score in game.killers.items()]),
		) + (f'\n\n*{error_message}*' if error_message else ""),
		menu['buttons']
	)


def distribute_prizes(context, game):
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


@with_admin_rights
def mailing(update, context, menu):
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


def spam(context):
	user_id, spam_message = context.job.context
	try:
		context.bot.send_message(user_id, spam_message)
	except Exception as err:
		logger.error('Sending message to {} failed because: {}, {}'.format(
			user_id, type(err).__name__, err.args))


##############################

admin_menu['callback'] = admin_main
admin_menu['next']['mailing']['callback'] = mailing

manage_admins_menu['next']['add_admin']['callback'] = add_admin
manage_admins_menu['next']['del_admin']['callback'] = revoke_admin

manage_matches_menu['callback'] = manage_matches
manage_matches_menu['next']['set_game_id_']['callback'] = set_game_id
manage_matches_menu['next']['set_winners_']['callback'] = set_winners
manage_matches_menu['next']['set_winners_']['next']['place_']['callback'] = set_each_winner
manage_matches_menu['next']['set_winners_']['next']['set_killers_']['callback'] = set_killers
