from datetime import datetime, timedelta
from logging import getLogger

from telegram import InlineKeyboardMarkup

import texts
import database
import buttons
from slot import Slot
from menu import MenuHandler

###############

logger = getLogger(__name__)


def updatePlayer(context, player_id, money, message):
	player_user_data = context.dispatcher.user_data.get(player_id)
	player_chat_data = context.dispatcher.chat_data.get(player_id)
	database.updateBalance(player_id, money)
	player_user_data['balance'] += money
	player_chat_data.setdefault('old_messages', []).append(
		context.bot.send_message(player_id, message))


def startGame(context):
	slot = context.job.context
	if not slot.ready():
		logger.info(f"Game {slot.slot_id} - {str(slot)} canceled")
		for player_id in slot.paying_players:
			updatePlayer(
				context, player_id, int(slot.settings['bet']),
				texts.match_canceled.format(str(slot))
			)
	else:
		logger.info(f"Game {slot.slot_id} - {str(slot)} started")
		context.bot_data.setdefault('running_games', set()).add(slot)


def manageSlot(slot, context):
	logger.info(f"Slot {slot.slot_id} expired, players: {len(slot.players)}")
	for player_id in slot.players:
		player_user_data = context.dispatcher.user_data.get(player_id)
		player_user_data['picked_slots'].discard(slot)
		# if not slot.full():
		# 	continue
		player_chat_data = context.dispatcher.chat_data.get(player_id)
		confirm_button = []
		message_text = texts.main['next']['pay_for_game']['msg'].format(
			game=str(slot),
			balance=player_user_data['balance'],
			bet=slot.settings['bet']
		)
		if player_user_data['balance'] < int(slot.settings['bet']):
			message_text += texts.too_expensive_match
		else:
			confirm_button = [buttons.createButtons(
				texts.main['next']['pay_for_game'], f'confirm_{slot.slot_id}'
			)]
		player_chat_data.setdefault('old_messages', []).append(
			context.bot.send_message(
				player_id, message_text,
				reply_markup=InlineKeyboardMarkup(
					[confirm_button] + texts.main['next']['pay_for_game']['buttons'])
			)
		)
		player_user_data['awaiting_payment'] = slot
		player_chat_data['history'] = ['confirm_participation']
		context.job_queue.run_once(startGame, slot.time, context=slot)


def checkSlots(context):
	now = datetime.now()
	slots = context.bot_data.setdefault('slots', [])
	for index, slot in enumerate(slots):
		if slot.full() or slot.time <= now + timedelta(minutes=15):
			ready_slot = slots.pop(index)
			if ready_slot.time + timedelta(hours=1) < now:
				slots.insert(index, Slot(ready_slot.time))
			manageSlot(ready_slot, context)
	if slots:
		next_slot_time = slots[-1].time
	else:
		next_slot_time = now.replace(minute=0 if now.minute < 30 else 30, second=0)
	while len(slots) < 24:
		next_slot_time += timedelta(minutes=1)
		slots.append(Slot(next_slot_time))


def checkGames(context):
	running_games = context.bot_data.get('running_games', [])
	for game in running_games:
		if game.done():
			winners = game.payout()
			for winner_id, place, prize in winners:
				updatePlayer(
					context, winner_id, prize,
					texts.victory.format(place, prize)
				)
			running_games.discard(game)
			logger.info(f"Game ended winners are: {winners}")


def scheduleJobs(job_queue):
	job_queue.run_repeating(checkSlots, timedelta(seconds=5), first=0)
	job_queue.run_repeating(checkGames, timedelta(seconds=9), first=0)
	logger.info("Jobs scheduled")
