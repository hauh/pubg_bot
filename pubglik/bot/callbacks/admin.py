"""Admin menu"""

import re

from telegram import ChatAction, Document

from pubglik import database
from pubglik.bot.misc import excel

##############################


def with_admin_rights(admin_func):
	def check_rights(conversation, context):
		if not context.user_data.get('admin'):
			raise PermissionError(
				f"User id: {conversation.user_id}, "
				f"Telegram username: {context.user_data.get('username')}"
			)
		return admin_func(conversation, context)
	return check_rights


@with_admin_rights
def main(conversation, context):
	return conversation.reply(conversation.state.texts)


@with_admin_rights
def add_admin(conversation, context):
	if not conversation.input:
		return conversation.reply(conversation.state.texts['input'])

	if not conversation.confirmed:

		if not (user := database.find_user(username=conversation.input)):
			return conversation.reply(conversation.state.texts['not_found'])

		conversation.add_button(conversation.state.confirm_button(user['id']))
		return conversation.reply(
			conversation.state.texts['found'].format(user['username']))

	return switch_admin(conversation, context, True)


@with_admin_rights
def revoke_admin(conversation, context):
	if not conversation.confirmed:
		for admin in database.find_user(admin=True, fetch_all=True):
			conversation.add_button(
				conversation.state.extra['revoke'](admin['id'], admin['username']))
		return conversation.reply(conversation.state.texts)

	return switch_admin(conversation, context, False)


def switch_admin(conversation, context, new_state):
	admin_id = int(conversation.input)
	database.update_user(admin_id, admin=new_state)
	context.dispatcher.user_data[admin_id]['admin'] = new_state
	conversation.set_answer(conversation.state.answers['success'])
	return conversation.back(context)


@with_admin_rights
def manage_tournaments(conversation, context):
	for game in context.bot_data.get('games', []):
		if not game.is_running:
			conversation.add_button(conversation.state.extra['set_room'](game))
		elif not game.is_finished:
			conversation.add_button(conversation.state.extra['set_winners'](game))
	return conversation.reply(conversation.state.texts)


def with_game_to_manage(manage_game_func):
	def find_game(conversation, context):
		game_id = context.user_data.setdefault(
			'game_to_manage', int(conversation.data))
		for game in context.bot_data.get('games', []):
			if not game.is_finished and game.slot_id == game_id:
				return manage_game_func(conversation, context, game)
		# noqa todo: warning if not found
		del context.user_data['game_to_manage']
		return manage_tournaments(conversation, context)
	return find_game


@with_admin_rights
@with_game_to_manage
def set_room(conversation, context, game):
	if not conversation.input:
		return conversation.reply(conversation.texts['input'].format(
			str(game), game.room_id, game.room_pass))

	# input should be in 'pubg_id,pass' format
	try:
		pubg_id, room_pass = conversation.input.split(',')
		pubg_id = int(pubg_id)
	except ValueError:
		return conversation.reply(conversation.state.texts['invalid'])

	if not conversation.confirmed:
		room_pass = room_pass.strip()
		conversation.add_button(
			conversation.state.confirm_button(f'{pubg_id},{room_pass}'))
		return conversation.reply(
			conversation.state.texts['confirm'].format(pubg_id, room_pass))

	game.run_game(pubg_id, room_pass)
	conversation.set_answer(conversation.state.answers['success'])
	del context.user_data['game_to_manage']
	return conversation.back(context)


@with_admin_rights
@with_game_to_manage
def set_winners(conversation, context, game):
	if not conversation.confirmed:
		context.bot.send_chat_action(conversation.user_id, ChatAction.TYPING)
		conversation.add_button(
			conversation.state.extra['generate_table'](game.slot_id))
		game.reset_results()

		# first asking for filled table
		if not isinstance(conversation.input, Document):
			return conversation.reply(
				conversation.state.texts['input'].format(str(game), game.room_id))

		# then trying to read xlsx file
		if not (results := excel.read_table(conversation.input.get_file())):
			return conversation.reply(conversation.state.texts['bad_file'])

		# reading file for places and kills
		try:
			if hasattr(game.game, 'places'):
				for row, user_id, place in excel.get_winners(results):
					game.game.set_player_place(user_id, place)
			if hasattr(game.game, 'kills'):
				for row, user_id, kills in excel.get_killers(results):
					game.game.set_player_kills(user_id, kills)
		except ValueError as err:
			return conversation.reply(
				conversation.state.texts[err.args[0]]. format(row))

		if not game.winners_are_set:
			return conversation.reply(conversation.texts['missing_something'])

		# if table filled correctly, preparing distribution and asking to confirm
		total_payouts = game.distribute_prizes()
		conversation.add_button(conversation.state.confirm_button(game.slot_id))
		return conversation.reply(conversation.state.texts['confirm'].format(
			game.prize_fund, total_payouts))

	# if winners are set and confirmed mark game as finished for job worker
	game.is_finished = True
	conversation.set_answer(conversation.answers['success'])
	del context.user_data['game_to_manage']
	return conversation.back(context)


@with_admin_rights
@with_game_to_manage
def generate_table(conversation, context, game):
	context.bot.send_chat_action(conversation.user_id, ChatAction.TYPING)
	context.bot.send_document(
		conversation.user_id,
		excel.create_table(database.get_players(game.slot_id)),
		filename=f'{game.pubg_id}.xlsx'
	)
	return conversation.back(context)


@with_admin_rights
def manage_users(conversation, context):
	if conversation.input:
		try:
			user_id = int(conversation.input)
		except ValueError:
			if conversation.input.startswith('@'):
				user = database.find_user(username=conversation.input[1:])
			else:
				user = database.find_user(pubg_username=conversation.input)
		else:
			if not (user := database.find_user(pubg_id=user_id)):
				user = database.find_user(id=user_id)
		if not user:
			context.user_data.pop('user_to_manage', None)
			return conversation.reply(conversation.state.texts['not_found'])

		context.user_data['user_to_manage'] = user

	elif not (user := context.user_data.get('user_to_manage')):
		return conversation.reply(conversation.state.texts['input'])

	user_id = user['id']
	user['balance'] = database.get_balance(user_id)
	context.dispatcher.user_data.setdefault(user_id, {}).update(user)
	conversation.add_button(conversation.state.extra['change_balance'])
	conversation.add_button(
		conversation.state.extra['ban_user'] if not user['banned']
		else conversation.state.extra['unban_user']
	)
	return conversation.reply(conversation.state.texts['found'].format(**user))


@with_admin_rights
def change_balance(conversation, context):
	user = context.user_data['user_to_manage']

	if not conversation.confirmed:
		if not conversation.input:
			return conversation.reply(conversation.state.texts['input'].format(**user))

		if not re.match(r'^-?[1-9][0-9]{0,5}$', conversation.input):
			return conversation.reply(conversation.state.texts['invalid'])

		conversation.add_button(
			conversation.state.confirm_button(conversation.input))
		return conversation.reply(
			conversation.state.texts['confirm'].format(conversation.input))

	amount = int(conversation.input)
	conversation.input = None
	user['balance'] = database.change_balance(
		user['id'], amount, 'by_admin', ext_id=conversation.user_id)
	conversation.set_answer(conversation.state.answers['success'])
	return conversation.back(context)


@with_admin_rights
def unban_user(conversation, context):
	user = context.user_data['user_to_manage']
	database.update_user(user['id'], banned=False)
	user['banned'] = False
	conversation.set_answer(conversation.state.answers['success'])
	return conversation.back(context)


@with_admin_rights
def ban_user(conversation, context):
	if not conversation.confirmed:
		conversation.add_button(conversation.state.confirm_button('ban'))
		return conversation.reply(conversation.state.texts)

	user = context.user_data['user_to_manage']
	banned_user_id = user['id']
	database.update_user(banned_user_id, banned=True)
	user['banned'] = True
	# ugly
	if (user_conversation := context.dispatcher.handlers[0][0]
	.user_conversations.pop(banned_user_id, None)):
		user_conversation.clear()
	for slot in user.pop('picked_slots', []):
		slot.leave(banned_user_id)

	conversation.set_answer(conversation.state.answers['success'])
	return conversation.back(context)


@with_admin_rights
def mailing(conversation, context):
	spam_message = context.user_data.get('message_to_spam')

	if not conversation.confirmed:
		if conversation.input:
			context.user_data['message_to_spam'] = conversation.input
			spam_message = conversation.input

		elif not spam_message:
			return conversation.reply(conversation.state.texts['input'])

		conversation.add_button(conversation.state.confirm_button('spam'))
		return conversation.reply(
			conversation.state.texts['confirm'].format(spam_message))

	for user in database.find_user(admin=False, banned=False, fetch_all=True):
		context.bot.send_message(user['id'], spam_message)
	conversation.set_answer(conversation.state.answers['success'])
	return conversation.back(context)


@with_admin_rights
def bot_settings(conversation, context):
	conversation.add_button(
		conversation.state.extra['debug_on'] if not context.bot.debug_mode
		else conversation.state.extra['debug_off']
	)
	return conversation.reply(conversation.state.texts)


@with_admin_rights
def debug_mode(conversation, context):
	context.bot.switch_debug_mode()
	conversation.set_answer(
		conversation.state.answers['debug_on'] if context.bot.debug_mode
		else conversation.state.answers['debug_off']
	)
	return conversation.back(context)
