from datetime import datetime, timedelta
from logging import getLogger

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import config
import texts
import database
from slot import Slot

###############

logger = getLogger(__name__)

CLOSE_TIME = timedelta(minutes=config.times['close_slot'])
SLOT_INTERVAL = timedelta(minutes=config.times['slot_interval'])
SEND_ROOM_BEFORE = timedelta(minutes=config.times['send_room'])
DELETE_SLOT_MESSAGE_TIME = timedelta(hours=3)

goto_admin_button = InlineKeyboardMarkup(
	[[InlineKeyboardButton(texts.goto_admin, callback_data='manage_matches')]])


def check_slots(context):
	now = datetime.now(config.timezone)
	waiting_slots = []

	for slot in context.bot_data.setdefault('slots', []):
		# requesting room id and pass and waiting for start
		if slot.is_ready:
			messages = [context.bot.send_message(
				config.admin_group_id,
				texts.slot_ready.format(str(slot)),
				reply_markup=goto_admin_button
			)]
			warning_time = slot.time - SEND_ROOM_BEFORE
			message_text = texts.match_is_starting_soon.format(str(slot))
			for user_id in slot.players:
				messages.append(context.bot.send_message(user_id, message_text))
			context.job_queue.run_once(
				_delete_game_messages, warning_time, context=messages)
			context.job_queue.run_once(
				_start_game, warning_time, context=slot)
			logger.info(f"Slot [{str(slot)}] is ready, waiting for room and pass")

		# deleting expired slot
		elif slot.time + CLOSE_TIME >= now:
			_delete_slot(context, slot)

		# waiting for the right time
		else:
			waiting_slots.append(slot)

	# filling waiting slots with new ones
	if len(waiting_slots) < 24:
		next_slot_time = (now + timedelta(minutes=30)).replace(
			minute=0 if now.minute < 30 else 30, second=0, microsecond=0)
		while len(waiting_slots) < 24:
			next_slot_time += SLOT_INTERVAL
			waiting_slots.append(Slot(next_slot_time))

	context.bot_data['slots'] = waiting_slots


def check_games(context):
	running_games = []

	for game in context.bot_data.setdefault('games', []):
		# waiting for results
		if not game.finished:
			running_games.append(game)
			continue

		# sending rewards
		total_payouts = 0
		for user_id, prize, place, kills in game.reward():
			player_data = context.dispatcher.user_data.get(user_id)
			player_data['balance'] += prize
			player_data['picked_slots'].discard(game)
			total_payouts += prize
			context.bot.send_message(
				user_id,
				texts.victory.format(
					game=str(game),
					place=texts.winner_place.format(place) if place else "",
					kills=texts.kills_count.format(kills) if kills else "",
					prize=prize
				)
			)
		context.bot.send_message(
			config.admin_group_id,
			texts.match_ended.format(
				game=str(game), pubg_id=game.pubg_id,
				total_bets=game.prize_fund, prizes=total_payouts
			)
		)
		logger.info(
			f"Game {game.slot_id} (PUBG ID {game.pubg_id}) finished, "
			f"total bets: {game.prize_fund}, payouts: {total_payouts}"
		)
		del game

	context.bot_data['games'] = running_games


def _start_game(context):
	game = context.job.context
	if not game.is_room_set:
		logger.error(
			f"Game {game.slot_id} - {str(game)} canceled "
			"because no room for it was created!"
		)
		context.bot.send_message(
			config.admin_group_id,
			texts.match_failed.format(str(game))
		)
		return _delete_slot(context, game)

	messages = [context.bot.send_message(
		config.admin_group_id,
		texts.match_started.format(str(game), game.pubg_id)
	)]
	message_text = texts.match_is_nigh.format(
		slot=str(game), room_name=game.pubg_id, room_pass=game.room_pass)
	for user_id in game.players:
		messages.append(context.bot.send_message(user_id, message_text))
	context.job_queue.run_once(
		_delete_game_messages, DELETE_SLOT_MESSAGE_TIME, context=messages)
	context.bot_data.setdefault('games', []).append(game)
	logger.info(f"Game {game.slot_id} - {str(game)} started!")


def _delete_slot(context, slot):
	database.delete_slot(slot.slot_id)
	message_text = texts.match_didnt_happen.format(str(slot))
	messages = []
	for user_id in slot.players:
		player_data = context.dispatcher.user_data.get(user_id)
		player_data['balance'] += slot.bet
		player_data['picked_slots'].discard(slot)
		messages.append(context.bot.send_message(user_id, message_text))
		context.job_queue.run_once(
			_delete_game_messages, DELETE_SLOT_MESSAGE_TIME, context=messages)
	del slot


def _delete_game_messages(context):
	for message in context.job.context:
		try:
			message.delete()
		except Exception:
			pass
