from datetime import datetime, timedelta
from logging import getLogger

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import config
import texts
import database
from slot import Slot

###############

logger = getLogger(__name__)


def checkSlots(context):
	now = datetime.now()
	slots = context.bot_data.setdefault('slots', [])
	for index, slot in enumerate(slots):
		if slot.is_ready or slot.time <= now + timedelta(minutes=20):
			ready_slot = slots.pop(index)
			if ready_slot.time + timedelta(hours=1) < now:
				slots.insert(index, Slot(ready_slot.time))
			manageSlot(ready_slot, context)
	if slots:
		next_slot_time = slots[-1].time
	else:
		next_slot_time = now.replace(minute=0 if now.minute < 30 else 30, second=0)
	while len(slots) < 24:
		next_slot_time += timedelta(minutes=30)
		slots.append(Slot(next_slot_time))
	context.bot_data['running_games'] = set(slots)


def manageSlot(slot, context):
	logger.info(f"Slot {slot.slot_id} expired, players: {len(slot.players)}")
	ready = slot.is_ready
	if ready:
		context.bot.send_message(
			config.admin_group_id, texts.pubg_id_is_needed.format(str(slot)),
			reply_markup=InlineKeyboardMarkup(
				[[InlineKeyboardButton(texts.goto_admin, callback_data='manage_matches')]])
		)
		context.bot_data.setdefault('pending_games', set()).add(slot)
		delay = slot.time - datetime.now() - timedelta(minutes=5)
		context.job_queue.run_once(startGame, delay, context=slot)
	for player_id in slot.players:
		player_data = context.dispatcher.user_data.get(player_id)
		if not ready:
			player_data['balance'] = database.updateBalance(player_id, slot.bet)
			msg = texts.match_didnt_happen.format(str(slot))
			context.job_queue.run_once(
				delGameMessage, timedelta(days=1), context=player_id)
		else:
			msg = texts.match_is_starting_soon.format(str(slot))
		player_data['game_message'] = context.bot.send_message(player_id, msg)
		player_data['picked_slots'].discard(slot)


def startGame(context):
	slot = context.job.context
	context.bot_data.get('pending_games').discard(slot)
	ready = True if slot.pubg_id else False
	if not ready:
		logger.warning(
			f"Game {slot.slot_id} - {str(slot)} canceled "
			"because no PUBG ID was provided!"
		)
		msg = texts.match_didnt_happen.format(str(slot))
	else:
		logger.info(f"Game {slot.slot_id} - {str(slot)} started!")
		msg = texts.match_is_nigh.format(slot.pubg_id)
		context.bot_data.setdefault('running_games', set()).add(slot)
		context.bot.send_message(
			config.admin_group_id,
			texts.match_has_started.format(str(slot), slot.pubg_id)
		)
	for player_id in slot.players:
		player_data = context.dispatcher.user_data.get(player_id)
		player_data['game_message'].delete()
		player_data['game_message'] = context.bot.send_message(player_id, msg)
		if not ready:
			context.job_queue.run_once(
				delGameMessage, timedelta(days=1), context=player_id)
			player_data['balance'] = database.updateBalance(player_id, slot.bet)


def delGameMessage(context):
	player_id = context.job.context
	player_data = context.dispatcher.user_data.get(player_id)
	player_data.pop('game_message').delete()
