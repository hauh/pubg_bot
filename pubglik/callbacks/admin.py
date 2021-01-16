"""Admin menu"""

import re
from functools import partial

from telegram import ChatAction, Document

from pubglik import database
from . import _excel

##############################


def with_admin_rights(admin_func):
	def check_rights(state, conversation, context):
		if not context.user_data.get('admin'):
			raise PermissionError(
				f"User id: {conversation.user_id}, "
				f"Telegram username: {context.user_data.get('username')}"
			)
		return admin_func(state, conversation, context)
	return check_rights


@with_admin_rights
def main(state, conversation, context):
	return conversation.reply()


@with_admin_rights
def add_admin(state, conversation, context):
	if not conversation.input:
		return conversation.reply(state.texts['input'])

	if not conversation.confirmed:

		if not (user := database.find_user(username=conversation.input)):
			return conversation.reply(state.texts['not_found'])

		return conversation.reply(
			text=state.texts['found'].format(user['username']),
			confirm=user['id']
		)

	return switch_admin(conversation, context, True)


@with_admin_rights
def revoke_admin(state, conversation, context):
	if not conversation.confirmed:
		return conversation.reply(
			extra_buttons=[state.extra['revoke'](admin['id'], admin['username'])
				for admin in database.find_user(admin=True, fetch_all=True)]
		)

	return switch_admin(conversation, context, False)


def switch_admin(conversation, context, new_state):
	admin_id = int(conversation.input)
	database.update_user(admin_id, admin=new_state)
	context.dispatcher.user_data[admin_id]['admin'] = new_state
	return conversation.back(context, answer='success')


@with_admin_rights
def manage_tournaments(state, conversation, context):
	game_buttons = []
	for game in context.bot_data.get('games', []):
		if not game.is_running:
			game_buttons.append(state.extra['set_room'](game))
		elif not game.is_finished:
			game_buttons.append(state.extra['set_winners'](game))
	return conversation.reply(extra_buttons=game_buttons)


def with_game_to_manage(manage_game_func):
	def find_game(state, conversation, context):
		game_id = context.user_data.setdefault(
			'game_to_manage', int(conversation.data))
		for game in context.bot_data.get('games', []):
			if not game.is_finished and game.slot_id == game_id:
				return manage_game_func(conversation, context, game)
		# noqa todo: warning if not found
		del context.user_data['game_to_manage']
		return manage_tournaments(state, conversation, context)
	return find_game


@with_admin_rights
@with_game_to_manage
def set_room(state, conversation, context, game):
	if not conversation.input:
		return conversation.reply(
			conversation.texts['input'].format(str(game), game.room_id, game.room_pass))

	# input should be in 'pubg_id,pass' format
	try:
		pubg_id, room_pass = conversation.input.split(',')
		pubg_id = int(pubg_id)
	except ValueError:
		return conversation.reply(state.texts['invalid'])

	if not conversation.confirmed:
		room_pass = room_pass.strip()
		return conversation.reply(
			text=state.texts['confirm'].format(pubg_id, room_pass),
			confirm=f'{pubg_id},{room_pass}'
		)

	game.run_game(pubg_id, room_pass)
	del context.user_data['game_to_manage']
	return conversation.back(context, answer='success')


@with_admin_rights
@with_game_to_manage
def set_winners(state, conversation, context, game):
	if not conversation.confirmed:
		conversation.update.effective_chat.send_action(ChatAction.TYPING)
		reply_with_excel_button = partial(conversation.reply,
			extra_buttons=(state.extra['generate_table'](game.slot_id),))
		game.reset_results()

		# first asking for filled table
		attachement = conversation.update.effective_message.effective_attachement
		if not attachement or not isinstance(attachement, Document):
			return reply_with_excel_button(
				state.texts['input'].format(str(game), game.room_id))

		# then trying to read xlsx file
		if not (results := _excel.read_table(attachement.get_file())):
			return conversation.reply(state.texts['bad_file'])

		# reading file for places and kills
		try:
			if hasattr(game.game, 'places'):
				for row, user_id, place in _excel.get_winners(results):
					game.game.set_player_place(user_id, place)
			if hasattr(game.game, 'kills'):
				for row, user_id, kills in _excel.get_killers(results):
					game.game.set_player_kills(user_id, kills)
		except ValueError as err:
			return reply_with_excel_button(state.texts[err.args[0]]. format(row))

		if not game.winners_are_set:
			return reply_with_excel_button(conversation.texts['missing_something'])

		# if table filled correctly, preparing distribution and asking to confirm
		total_payouts = game.distribute_prizes()
		return reply_with_excel_button(
			text=state.texts['confirm'].format(game.prize_fund, total_payouts),
			confirm=game.slot_id
		)

	# if winners are set and confirmed mark game as finished for job worker
	game.is_finished = True
	del context.user_data['game_to_manage']
	return conversation.back(context, answer='success')


@with_admin_rights
@with_game_to_manage
def generate_table(state, conversation, context, game):
	conversation.update.effective_chat.send_action(ChatAction.TYPING)
	conversation.update.effective_chat.send_document(
		_excel.create_table(database.get_players(game.slot_id)),
		filename=f'{game.pubg_id}.xlsx'
	)
	return conversation.back(context)


@with_admin_rights
def manage_users(state, conversation, context):
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
			return conversation.reply(state.texts['not_found'])

		context.user_data['user_to_manage'] = user

	elif not (user := context.user_data.get('user_to_manage')):
		return conversation.reply(state.texts['input'])

	user_id = user['id']
	user['balance'] = database.get_balance(user_id)
	context.dispatcher.user_data.setdefault(user_id, {}).update(user)
	return conversation.reply(
		text=state.texts['found'].format(**user),
		extra_buttons=(
			state.extra['change_balance'],
			state.extra['ban_user' if not user['banned'] else 'unban_user']
		)
	)


@with_admin_rights
def change_balance(state, conversation, context):
	user = context.user_data['user_to_manage']

	if not conversation.confirmed:
		if not conversation.input:
			return conversation.reply(state.texts['input'].format(**user))

		if not re.match(r'^-?[1-9][0-9]{0,5}$', conversation.input):
			return conversation.reply(state.texts['invalid'])

		return conversation.reply(
			text=state.texts['confirm'].format(conversation.input),
			confirm=conversation.input
		)

	amount = int(conversation.input)
	conversation.input = None
	user['balance'] = database.change_balance(
		user['id'], amount, 'by_admin', ext_id=conversation.user_id)
	return conversation.back(context, answer='success')


@with_admin_rights
def unban_user(state, conversation, context):
	user = context.user_data['user_to_manage']
	database.update_user(user['id'], banned=False)
	user['banned'] = False
	return conversation.back(context, answer='success')


@with_admin_rights
def ban_user(state, conversation, context):
	if not conversation.confirmed:
		return conversation.reply(confirm='ban')

	user = context.user_data['user_to_manage']
	banned_user_id = user['id']
	database.update_user(banned_user_id, banned=True)
	user['banned'] = True
	if user_conversation := user.get('conversation'):
		user_conversation.banned = True
		for message in user_conversation.messages:
			message.delete()
	for slot in user.pop('joined_slots', []):
		slot.leave(banned_user_id)

	return conversation.back(context, answer='success')


@with_admin_rights
def mailing(state, conversation, context):
	spam_message = context.user_data.get('message_to_spam')

	if not conversation.confirmed:
		if conversation.input:
			context.user_data['message_to_spam'] = conversation.input
			spam_message = conversation.input

		elif not spam_message:
			return conversation.reply(state.texts['input'])

		return conversation.reply(
			text=state.texts['confirm'].format(spam_message), confirm='spam')

	for user in database.find_user(admin=False, banned=False, fetch_all=True):
		context.bot.send_message(user['id'], spam_message)
	return conversation.back(context, answer='success')


@with_admin_rights
def bot_settings(state, conversation, context):
	return conversation.reply(extra_buttons=(
		state.extra['debug_on' if not context.bot.debug_mode else 'debug_off'],))


@with_admin_rights
def debug_mode(state, conversation, context):
	context.bot.switch_debug_mode()
	return conversation.back(
		context, answer='debug_on' if context.bot.debug_mode else 'debug_off')
