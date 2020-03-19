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
					slot=str(slot), pubg_id=slot.pubg_id),
				callback_data=f"set_game_id_{slot.slot_id}"
			)
		])
	for slot in running_games:
		buttons.append([
			InlineKeyboardButton(
				menu['next']['set_winners_']['btn_template'].format(
					slot=str(slot), pubg_id=slot.pubg_id),
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
		if context.user_data['history'][-1].startswith('set_game_id'):
			games = context.bot_data.get('pending_games', {})
		elif context.user_data['history'][-1].startswith('set_winners'):
			games = context.bot_data.get('running_games', {})
		data = context.user_data['history'][-1]
		game_id = int(data[data.rfind('_') + 1:])
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
		game.pubg_id = int(validated_input)
		answer = menu['input']['msg_success']
		update.callback_query.answer(answer, show_alert=True)
		del context.user_data['history'][-1:]
		return manageMatches(update, context)

	user_input = context.user_data.pop('user_input', None)
	if user_input:
		confirm_button = [InlineKeyboardButton(
			texts.confirm, callback_data=f'confirm_{user_input}')]
		message = menu['input']['msg_valid'].format(
			game=str(game), new_id=user_input)
	else:
		confirm_button = []
		message = menu['msg'].format(game=str(game), pubg_id=game.pubg_id)
	return (message, [confirm_button] + menu['buttons'])


@withAdminRights
@withExistingGame
def setWinners(update, context, menu, game):
	all_winner_set = context.user_data.pop('validated_input', None)
	if all_winner_set:
		distributePrizes(context, game)
		update.callback_query.answer(menu['input']['msg_success'], show_alert=True)
		del context.user_data['history'][-1:]
		return manageMatches(update, context)

	games_buttons = []
	if all(game.winners.values()):
		games_buttons.append(
			[InlineKeyboardButton(texts.confirm, callback_data='confirm_winners')])
	winners = ""
	for place, winner in game.winners.items():
		winner_username, kills = winner if winner else (None, 0)
		winner_description = menu['next']['place_']['btn_template'].format(
			place=place, username=winner_username, kills=kills)
		games_buttons.append([InlineKeyboardButton(
			winner_description,
			callback_data=f"place_{game.slot_id}_{place}"
		)])
		winners += winner_description
	return (
		menu['msg'].format(game=str(game), pubg_id=game.pubg_id, winners=winners),
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

	username, *kills = user_input.split(',')
	try:
		kills = int(kills[0])
	except Exception:
		kills = 0

	user = database.getUser(pubg_username=username)
	if not user:
		try:
			user = database.getUser(pubg_id=int(username))
		except Exception:
			pass

	running_games = context.bot_data.get('running_games', {})
	for game in running_games:
		if game.slot_id == game_id:
			if not user:
				game.winners[place] = texts.user_not_found
				return (menu['input']['msg_fail'], menu['buttons'])
			game.winners[place] = (user['pubg_username'], kills)
			del context.user_data['history'][-1:]
			return setWinners(
				update, context,
				admin_menu['next']['manage_matches']['next']['set_winners_']
			)

	del context.user_data['history'][-1:]
	return manageMatches(update, context)


def distributePrizes(context, game):
	for player_id in game.players:
		player_data = context.dispatcher.user_data.get(player_id)
		try:
			player_data.pop('game_message').delete()
		except Exception:
			pass
	winners, total_payouts = game.reward()
	for winner_id, place, prize in winners:
		winner_data = context.dispatcher.user_data.get(winner_id)
		winner_data['balance'] = database.updateBalance(winner_id, prize)
		winner_data['game_message'] = context.bot.send_message(
			winner_id, texts.victory.format(str(game), place, prize)
		)
	logger.info(f"Game ended, winners are: {winners}")
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
