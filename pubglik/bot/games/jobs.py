"""Jobs checking slots to start and games to run"""

from logging import getLogger
from datetime import datetime, timedelta

from pubglik import database
from pubglik.config import (
	times as TIMES,
	timezone as TIMEZONE,
	max_slots as MAX_SLOTS
)
from pubglik.bot import texts
from .slot import Slot

###############

logger = getLogger('jobs')

CLOSE_TIME = timedelta(minutes=TIMES['close_slot'])
SLOT_INTERVAL = timedelta(minutes=TIMES['slot_interval'])
SEND_ROOM_BEFORE = timedelta(minutes=TIMES['send_room'])
DELETE_SLOT_MESSAGE_TIME = timedelta(hours=3)


def restore_state(context):
	active_slots = []
	for match in database.restore_slots():
		slot = Slot(**match)
		for player in match['players']:
			player_id = player['id']
			slot.players[player_id] = dict()
			player_data = context.dispatcher.user_data.setdefault(player_id, player)
			if 'balance' not in player_data:
				player_data['balance'] = database.get_balance(player_id)
			player_data.setdefault('picked_slots', set()).add(slot)
		active_slots.append(slot)
	context.dispatcher.bot_data['slots'] = active_slots
	if active_slots:
		logger.info("%s slots restored from database", len(active_slots))


def check_slots_and_games(context):
	slot_expiration_time = datetime.now(TIMEZONE) + CLOSE_TIME
	waiting_slots = []
	running_games = []

	# checking waiting slots
	for slot in context.bot_data.setdefault('slots', []):
		# requesting room id and pass and schedule start
		if slot.is_ready:
			running_games.append(slot)
			context.bot.notify_admins(texts.slot_is_ready['admins'].format(str(slot)))
			next_step_time = slot.time - SEND_ROOM_BEFORE
			_alert_players(
				context, slot.players, next_step_time,
				texts.slot_is_ready['users'].format(str(slot))
			)
			context.job_queue.run_once(_start_game, next_step_time, context=slot)
			logger.info("Slot [%s] is waiting for room and pass", str(slot))

		# deleting expired slot
		elif slot.time <= slot_expiration_time:
			_delete_slot(context, slot)

		# waiting for the right time
		else:
			if not slot.players and slot.is_set:
				slot.reset_settings()
			waiting_slots.append(slot)

	# filling waiting slots with new ones
	while len(waiting_slots) < MAX_SLOTS:
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
			player_data['games_played'] += 1
			player_data['picked_slots'].discard(game)
			total_payouts += prize
			context.bot.send_message(
				user_id,
				texts.game_ended['users'].format(
					game=str(game),
					place=texts.winner_place.format(place) if place else "",
					kills=texts.kills_count.format(kills) if kills else "",
					prize=prize
				)
			)
		context.bot.notify_admins(
			texts.game_ended['admins'].format(
				game=str(game), pubg_id=game.pubg_id,
				total_bets=game.prize_fund, prizes=total_payouts
			)
		)
		logger.info(
			"Game %s (PUBG ID %s) finished, total bets: %s, payouts: %s",
			game.slot_id, game.pubg_id, game.prize_fund, total_payouts
		)

	context.bot_data['games'] = running_games


def _start_game(context):
	if (game := context.job.context).is_room_set:
		context.bot.notify_admins(
			texts.game_is_starting['admins'].format(str(game), game.pubg_id))
		_alert_players(
			context, game.players, DELETE_SLOT_MESSAGE_TIME,
			texts.game_is_starting['users'].format(
				str(game), game.pubg_id, game.room_pass)
		)
		logger.info("Game %s - %s started!", game.slot_id, str(game))

	else:
		context.bot.notify_admins(texts.game_failed.format(str(game)))
		_delete_slot(context, game)
		logger.error(
			"Game %s - %s canceled because no room for it was created!",
			game.slot_id, str(game)
		)


def _delete_slot(context, slot):
	slot.delete()
	for user_id in slot.players:
		player_data = context.dispatcher.user_data.get(user_id)
		player_data['balance'] += slot.bet
		player_data['picked_slots'].discard(slot)
	_alert_players(
		context, slot.players, DELETE_SLOT_MESSAGE_TIME,
		texts.game_didnt_happen.format(str(slot))
	)


def _alert_players(context, players, expires, text):
	alerts = []
	for player_id in players:
		context.bot.send_message(player_id, text, container=alerts)
	context.job_queue.run_once(
		lambda c: [message.delete() for message in c.job.context],
		expires, context=alerts
	)
