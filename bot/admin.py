import re
from logging import getLogger

import texts
import database
import excel
import utility

##############################

logger = getLogger(__name__)
admin_menu = texts.menu['next']['admin']
manage_admins_menu = admin_menu['next']['manage_admins']
manage_matches_menu = admin_menu['next']['manage_matches']


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
		elif where.startswith('set_winners'):
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
	def done(answer, *format_args, confirm=False):
		if confirm:
			confirm_button = utility.confirm_button('winners')
		else:
			confirm_button = []
			game.reset_winners()
		return (
			menu['answers'][answer].format(*format_args),
			[confirm_button] + menu['buttons']
		)

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

	# if no file was uploaded ask for winners table
	if not (file_upload := update.effective_message.document):
		return (menu['msg'], menu['buttons'])

	# trying to load xlsx file
	if not (results := excel.read_table(file_upload.get_file())):
		return done('bad_file')

	# reading file for places
	if game.type != 'kills':
		for user_id, place in excel.get_winners(results):
			if user_id not in game.players:
				return done('unknown_player', user_id)
			if place not in game.winning_places:
				return done('invalid_value', user_id)
			if user_id in game.winners.values():
				return done('duplicate_player', user_id)
			if game.winners.get(place) != user_id:
				return done('duplicate_place', user_id, place)
			game.winners[place] = user_id

	# reading file for kills
	if game.type != 'survival':
		possible_kills = range(1, game.players_count)
		for user_id, kills in excel.get_killers(results):
			if user_id not in game.players:
				return done('unknown_player', user_id)
			if kills not in possible_kills:
				return done('invalid_value', user_id)
			if game.killers.setdefault(user_id, kills) != kills:
				return done('duplicate_player', user_id)
		if game.total_kills != game.players_count - 1:
			return done('wrong_kills')

	if not game.winners_are_set:
		return done('not_enough_data')

	return done('confirm', confirm=True)


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
manage_matches_menu['next']['set_winners_']['callback'] = set_winners
manage_matches_menu['next']['set_game_id_']['callback'] = set_game_id
