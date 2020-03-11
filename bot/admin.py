from logging import getLogger

from telegram import InlineKeyboardButton

import texts
import config
import database

#######################

logger = getLogger(__name__)


def withAdminRights(admin_func):
	def checkRights(update, context, menu):
		if not context.user_data.get('admin')\
			and update.effective_user.id not in config.admin_id:
			return (None, None)
		return admin_func(update, context, menu)
	return checkRights


@withAdminRights
def mainAdmin(update, context, menu):
	return (menu['msg'], menu['buttons'])


def switchAdmin(update, context, admin_id, new_state):
	if database.updateAdmin(admin_id, new_state):
		answer = texts.admin_added if new_state is True else texts.admin_removed
		context.dispatcher.user_data[admin_id]['admin'] = new_state
	else:
		answer = texts.admin_update_failed
	update.callback_query.answer(answer, show_alert=True)
	del context.user_data['history'][-2:]
	return mainAdmin(update, context, texts.menu['next']['admin'])


@withAdminRights
def addAdmin(update, context, menu):
	validated_input = context.user_data.pop('validated_input', None)
	if validated_input:
		return switchAdmin(update, context, validated_input, True)

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
		return switchAdmin(update, context, validated_input, False)

	admins = database.getAdmins()
	admins_buttons = []
	admins_list = ""
	for admin in admins:
		admins_buttons.append([InlineKeyboardButton(
			f"@{admin['username']}", callback_data=f"confirm_{admin['id']}")])
		admins_list += f"@{admin['username']}\n"
	return (menu['msg'].format(admins_list), admins_buttons + menu['buttons'])


@withAdminRights
def manageMatches(update, context, menu):
	pending_games = context.bot_data.get('pending_games', [])
	running_games = context.bot_data.get('running_games', [])
	buttons = []
	for game in pending_games:
		buttons.append(
			[InlineKeyboardButton(
				f"{texts.set_pubg_id}: {game.slot_id} - {game.time_string} \
					- PUBG ID: ({game.pubg_id})",
				callback_data=f"set_game_id_{game.slot_id}")]
		)
	for game in running_games:
		buttons.append(
			[InlineKeyboardButton(
				f"{texts.set_slot_winners}: {game.slot_id} - {game.time_string} \
					- PUBG ID: ({game.pubg_id})",
				callback_data=f"set_winners_{game.slot_id}")]
		)
	return (
		menu['msg'].format(
			pending='\n'.join(str(game) for game in pending_games)
				if pending_games else menu['default'],
			running='\n'.join(str(game) for game in running_games)
				if running_games else menu['default']
		),
		buttons + menu['buttons']
	)


@withAdminRights
def setGameID(update, context, menu):
	pending_games = context.bot_data.get('pending_games', {})
	game_to_set_id = int(update.callback_query.data.lstrip('set_game_id_'))
	game_to_set = None
	for game in pending_games:
		if game.slot_id == game_to_set_id:
			game_to_set = game
			break
	validated_input = context.user_data.pop('validated_input', None)

	if not game_to_set or validated_input:
		if not game_to_set:
			answer = menu['input']['msg_error']
		elif validated_input:
			game.pubg_id = int(validated_input)
			answer = menu['input']['msg_success']
		update.callback_query.answer(answer, show_alert=True)
		del context.user_data['history'][-1:]
		return manageMatches(
			update, context, texts.menu['next']['admin']['next']['manage_matches'])

	user_input = context.user_data.pop('user_input', None)
	if user_input:
		confirm_button = [InlineKeyboardButton(
			texts.confirm, callback_data=f'confirm_{user_input}')]
		message = menu['input']['msg_valid'].format(
			game=str(game_to_set), new_id=user_input)
	else:
		confirm_button = []
		message = menu['msg'].format(game=str(game_to_set), pubg_id=game.pubg_id)
	return (message, [confirm_button] + menu['buttons'])


@withAdminRights
def setWinners(update, context, menu):
	pass
