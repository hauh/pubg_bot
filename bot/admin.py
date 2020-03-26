import re
from logging import getLogger

from telegram import InlineKeyboardButton

import texts
import config
import database

#######################

logger = getLogger(__name__)
admin_menu = texts.menu['next']['admin']


def withAdminRights(admin_func):
	def checkRights(update, context, menu=None):
		if not context.user_data.get('admin')\
			and update.effective_user.id not in config.admin_id:
			return (None, None)
		return admin_func(update, context, menu if menu else admin_func.__defaults__[0])
	return checkRights


@withAdminRights
def mainAdmin(update, context, menu=admin_menu):
	return (menu['msg'], menu['buttons'])


@withAdminRights
def addAdmin(update, context, menu):
	validated_input = context.user_data.pop('validated_input', None)
	if validated_input:
		return switchAdmin(update, context, menu, validated_input, True)

	user_input = context.user_data.pop('user_input', None)
	confirm_button = []
	if not user_input:
		message = menu['msg']
	else:
		admin = database.getUser(username=user_input)
		if admin:
			message = menu['input']['msg_valid'].format(admin['username'])
			confirm_button = [InlineKeyboardButton(
				texts.confirm, callback_data=f"confirm_{admin['id']}")]
		else:
			message = menu['input']['msg_error']
	return (message, [confirm_button] + menu['buttons'])


@withAdminRights
def delAdmin(update, context, menu):
	validated_input = context.user_data.pop('validated_input', None)
	if validated_input:
		return switchAdmin(update, context, menu, validated_input, False)

	admins = database.getAdmins()
	admins_buttons = []
	admins_list = ""
	for admin in admins:
		admins_buttons.append([InlineKeyboardButton(
			f"@{admin['username']}", callback_data=f"confirm_{admin['id']}")])
		admins_list += f"@{admin['username']}\n"
	return (menu['msg'].format(admins_list), admins_buttons + menu['buttons'])


def switchAdmin(update, context, menu, admin_id, new_state):
	if database.updateAdmin(admin_id, new_state):
		context.dispatcher.user_data[admin_id]['admin'] = new_state
		update.callback_query.answer(menu['input']['msg_success'], show_alert=True)
	else:
		update.callback_query.answer(menu['input']['msg_fail'], show_alert=True)
	del context.user_data['history'][-2:]
	return mainAdmin(update, context)


@withAdminRights
def manageMatches(update, context, menu=admin_menu['next']['manage_matches']):
	pending_games = context.bot_data.get('pending_games', [])
	running_games = context.bot_data.get('running_games', [])

	buttons = []
	for slot in pending_games:
		buttons.append([
			InlineKeyboardButton(
				menu['next']['set_game_id_']['btn_template'].format(
					game=str(slot), pubg_id=slot.pubg_id, room_pass=slot.room_pass),
				callback_data=f"set_game_id_{slot.slot_id}"
			)
		])
	for slot in running_games:
		buttons.append([
			InlineKeyboardButton(
				menu['next']['set_winners_']['btn_template'].format(
					game=str(slot), pubg_id=slot.pubg_id, room_pass=slot.room_pass),
				callback_data=f"set_winners_{slot.slot_id}"
			)
		])
	return (
		menu['msg'].format(
			pending='\n'.join(str(game) for game in pending_games)
				if pending_games else menu['default'],
			running='\n'.join(str(game) for game in running_games)
				if running_games else menu['default']
		),
		buttons + menu['buttons']
	)


def withExistingGame(manage_match_func):
	def checkGame(update, context, menu):
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
		return manageMatches(update, context)
	return checkGame


@withAdminRights
@withExistingGame
def setGameID(update, context, menu, game):
	validated_input = context.user_data.pop('validated_input', None)
	if validated_input:
		game.pubg_id, game.room_pass = validated_input.split(',')
		answer = menu['input']['msg_success']
		update.callback_query.answer(answer, show_alert=True)
		del context.user_data['history'][-1:]
		return manageMatches(update, context)

	confirm_button = []
	user_input = context.user_data.pop('user_input', None)
	if not user_input:
		message = menu['msg'].format(
			game=str(game), pubg_id=game.pubg_id, room_pass=game.room_pass)
	else:
		user_input = user_input.split(',')
		if len(user_input) != 2:
			message = menu['input']['msg_error']
		else:
			confirm_button = [InlineKeyboardButton(
				texts.confirm, callback_data=f'confirm_{user_input[0]},{user_input[1]}')]
			message = menu['input']['msg_valid'].format(
				game=str(game), pubg_id=user_input[0], room_pass=user_input[1])
	return (message, [confirm_button] + menu['buttons'])


@withAdminRights
@withExistingGame
def setWinners(update, context, menu, game):
	all_winner_set = context.user_data.pop('validated_input', None)
	if all_winner_set:
		update.callback_query.answer(menu['input']['msg_success'], show_alert=True)
		del context.user_data['history'][-1:]
		distributePrizes(context, game)
		return manageMatches(update, context)

	games_buttons = []
	if game.winners_are_set:
		games_buttons.append(
			[InlineKeyboardButton(texts.confirm, callback_data='confirm_winners')])
	winners = ""
	if game.game_type != 'kills':
		for place, winner in game.winners.items():
			winner_description = menu['next']['place_']['btn_template'].format(
				place=place, username=winner)
			games_buttons.append([InlineKeyboardButton(
				winner_description,
				callback_data=f"place_{game.slot_id}_{place}"
			)])
			winners += winner_description
	if game.game_type != 'survival':
		games_buttons.append([InlineKeyboardButton(
			menu['next']['set_killers_']['btn_template'],
			callback_data=f"set_killers_{game.slot_id}"
		)])
	return (
		menu['msg'].format(
			game=str(game),
			pubg_id=game.pubg_id,
			kills=game.total_kills,
			winners=winners
		),
		games_buttons + menu['buttons']
	)


@withAdminRights
def setEachWinner(update, context, menu):
	game_cb_data = update.callback_query.data.lstrip('place_').split('_')
	game_id = int(game_cb_data[0])
	place = int(game_cb_data[1])
	user_input = context.user_data.pop('user_input', None)
	if not user_input:
		return (menu['msg'].format(place), menu['buttons'])

	running_games = context.bot_data.get('running_games', {})
	for game in running_games:
		if game.slot_id == game_id:
			user = database.getPUBGUser(user_input)
			if not user:
				game.winners[place] = texts.user_not_found
				return (menu['input']['msg_fail'], menu['buttons'])

			game.winners[place] = user['pubg_username']
			del context.user_data['history'][-1:]
			return setWinners(
				update, context,
				admin_menu['next']['manage_matches']['next']['set_winners_']
			)

	del context.user_data['history'][-1:]
	return manageMatches(update, context)


@withAdminRights
@withExistingGame
def setKillers(update, context, menu, game):
	user_input = context.user_data.pop('user_input', None)
	error_message = None
	if user_input:
		if not re.match(r'^.+,[0-9][0-9]?$', user_input):
			error_message = menu['input']['msg_error']
		else:
			username, score = user_input.split(',')
			user = database.getPUBGUser(username)
			if not user:
				error_message = menu['input']['msg_fail']
			else:
				username = user['pubg_username']
				score = int(score)
				if username in game.killers.keys() and score == 0:
					del game.killers[username]
				elif game.total_kills + score >= len(game.players) - 1:
					error_message = menu['input']['msg_fail']
				else:
					game.killers[username] = score

	return (
		menu['msg'].format(
			kills=game.total_kills,
			killers="\n".join(
				[f'{killer} - {score}' for killer, score in game.killers.items()]),
		) + (f'\n\n*{error_message}*' if error_message else ""),
		menu['buttons']
	)


def distributePrizes(context, game):
	for player_id in game.players:
		player_data = context.dispatcher.user_data.get(player_id)
		try:
			player_data.pop('game_message').delete()
		except Exception:
			pass
	winners, total_payouts = game.reward()
	for winner_id, victory_message, prize in winners:
		winner_data = context.dispatcher.user_data.get(winner_id)
		winner_data['balance'] = database.updateBalance(winner_id, prize)
		winner_data['game_message'] = context.bot.send_message(
			winner_id,
			texts.victory.format(
				game=str(game), victory_message=victory_message, prize=prize)
		)
	logger.info(f"Game ended, winners are, payout: {total_payouts}")
	context.bot.send_message(
		config.admin_group_id,
		texts.match_has_ended.format(
			game=str(game),
			pubg_id=game.pubg_id,
			total_bets=game.prize_fund,
			prizes=total_payouts
		)
	)
	context.bot_data.get('running_games', set()).discard(game)


@withAdminRights
def mailing(update, context, menu):
	confirm_spam = context.user_data.pop('validated_input', None)
	if confirm_spam:
		users = database.getUser()
		for delay, user in enumerate(users):
			context.job_queue.run_once(
				spam, delay * 0.1,
				context=(user['id'], context.bot_data.get('spam_message'))
			)
		update.callback_query.answer(menu['input']['msg_success'])
		return mainAdmin(update, context)
	
	user_input = context.user_data.pop('user_input', None)
	if user_input:
		context.bot_data['spam_message'] = user_input
		confirm_button = [InlineKeyboardButton(
			texts.confirm, callback_data='confirm_spam')]
		return (
			menu['input']['msg_valid'].format(user_input),
			[confirm_button] + menu['buttons']
		)

	return (menu['msg'], menu['buttons'])
	

def spam(context):
	user_id, spam_message = context.job.context
	try:
		context.bot.send_message(user_id, spam_message)
	except Exception as err:
		logger.error('Sending message to {} failed because: {}, {}'.format(
			user_id, type(err).__name__, err.args))
