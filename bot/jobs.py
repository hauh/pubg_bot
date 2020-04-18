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
	now = datetime.now(config.timezone)
	slots = context.bot_data.setdefault('slots', [])
	for index, slot in enumerate(slots):
		if slot.is_ready or slot.time <= now + timedelta(minutes=config.times['close_slot']):
			ready_slot = slots.pop(index)
			if ready_slot.time + timedelta(hours=1) < now:
				slots.insert(index, Slot(ready_slot.time))
			manageSlot(ready_slot, context)
	if slots:
		next_slot_time = slots[-1].time
	else:
		next_slot_time = now + timedelta(minutes=5)
		# next_slot_time = (now + timedelta(minutes=30)).replace(
		# 	minute=0 if now.minute < 30 else 30, second=0, microsecond=0)
	while len(slots) < 24:
		next_slot_time += timedelta(minutes=config.times['slot_interval'])
		slots.append(Slot(next_slot_time))


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
		delay = slot.time - datetime.now(config.timezone) - timedelta(minutes=config.times['send_room'])
		context.job_queue.run_once(startGame, delay, context=slot)
	for player_id in slot.players:
		player_data = context.dispatcher.user_data.get(player_id)
		if not ready:
			player_data['balance'] = database.updateBalance(player_id, slot.bet, 'refund')
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
		logger.error(
			f"Game {slot.slot_id} - {str(slot)} canceled "
			"because no room for it was created!"
		)
		msg = texts.match_didnt_happen.format(str(slot))
	else:
		logger.info(f"Game {slot.slot_id} - {str(slot)} started!")
		msg = texts.match_is_nigh.format(
			slot=str(slot), room_name=slot.pubg_id, room_pass=slot.room_pass)
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
			player_data['balance'] = database.updateBalance(player_id, slot.bet, 'refund')


def delGameMessage(context):
	player_id = context.job.context
	player_data = context.dispatcher.user_data.get(player_id)
	player_data.pop('game_message').delete()
