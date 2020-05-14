'''Jobs checking slots to start and games to run'''

from logging import getLogger
from datetime import datetime, timedelta

import config
import texts
import database
import utility
from slot import Slot

###############

logger = getLogger('jobs')

CLOSE_TIME = timedelta(minutes=config.times['close_slot'])
SLOT_INTERVAL = timedelta(minutes=config.times['slot_interval'])
SEND_ROOM_BEFORE = timedelta(minutes=config.times['send_room'])
DELETE_SLOT_MESSAGE_TIME = timedelta(hours=3)


def check_slots_and_games(context):
	slot_expiration_time = datetime.now(config.timezone) + CLOSE_TIME
	waiting_slots = []
	running_games = []

	# checking waiting slots
	for slot in context.bot_data.setdefault('slots', []):
		# requesting room id and pass and waiting for start
		if slot.is_ready:
			running_games.append(slot)
			next_step_time = slot.time - SEND_ROOM_BEFORE
			utility.notify_admins(
				texts.slot_is_ready.format(str(slot)),
				context, expires=next_step_time
			)
			utility.notify(
				slot.players,
				texts.match_is_starting_soon.format(str(slot)),
				context, expires=next_step_time
			)
			context.job_queue.run_once(
				_start_game, next_step_time, context=slot)
			logger.info("Slot [%s] is waiting for room and pass", str(slot))

		# deleting expired slot
		elif slot.time <= slot_expiration_time:
			_delete_slot(context, slot)

		# waiting for the right time
		else:
			waiting_slots.append(slot)

	# filling waiting slots with new ones
	while len(waiting_slots) < 24:
		try:
			waiting_slots.append(Slot(waiting_slots[-1].time + SLOT_INTERVAL))
		except IndexError:
			waiting_slots.append(
				Slot((slot_expiration_time + timedelta(minutes=30)).replace(
					minute=0 if slot_expiration_time.minute < 30 else 30,
					second=0, microsecond=0)
				)
			)

	context.bot_data['slots'] = waiting_slots

	# checking games
	for game in context.bot_data.setdefault('games', []):
		# waiting for results
		if not game.is_finished:
			running_games.append(game)
			continue

		# sending rewards
		total_payouts = 0
		for user_id, prize, place, kills in game.reward():
			player_data = context.dispatcher.user_data.get(user_id)
			player_data['balance'] += prize
			player_data['picked_slots'].discard(game)
			total_payouts += prize
			utility.notify(
				[user_id],
				texts.victory.format(
					game=str(game),
					place=texts.winner_place.format(place) if place else "",
					kills=texts.kills_count.format(kills) if kills else "",
					prize=prize
				),
				context
			)
		utility.notify_admins(
			texts.match_ended.format(
				game=str(game), pubg_id=game.pubg_id,
				total_bets=game.prize_fund, prizes=total_payouts
			),
			context
		)
		logger.info(
			"Game %s (PUBG ID %s) finished, total bets: %s, payouts: %s",
			game.slot_id, game.pubg_id, game.prize_fund, total_payouts
		)
		del game

	context.bot_data['games'] = running_games


def _start_game(context):
	game = context.job.context
	if not game.is_room_set:
		logger.error(
			"Game %s - %s canceled because no room for it was created!",
			game.slot_id, str(game)
		)
		utility.notify_admins(texts.match_failed.format(str(game)), context)
		_delete_slot(context, game)
		return

	utility.notify_admins(
		texts.match_started.format(str(game), game.pubg_id),
		context, expires=DELETE_SLOT_MESSAGE_TIME
	)
	utility.notify(
		game.players,
		texts.match_is_nigh.format(str(game), game.pubg_id, game.room_pass),
		context, expires=DELETE_SLOT_MESSAGE_TIME
	)
	game.is_running = True
	context.bot_data.setdefault('games', []).append(game)
	logger.info("Game %s - %s started!", game.slot_id, str(game))


def _delete_slot(context, slot):
	database.delete_slot(slot.slot_id)
	for user_id in slot.players:
		player_data = context.dispatcher.user_data.get(user_id)
		player_data['balance'] += slot.bet
		player_data['picked_slots'].discard(slot)
	utility.notify(
		slot.players,
		texts.match_didnt_happen.format(str(slot)),
		context, expires=DELETE_SLOT_MESSAGE_TIME
	)
	del slot
