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


def startGame(context):
	slot = context.job.context
	ready = True if slot.pubg_id else False
	if ready:
		logger.warning(
			f"Game {slot.slot_id} - {str(slot)} canceled "
			"because no PUBG ID was provided!"
		)
		msg = texts.match_didnt_happen.format(str(slot))
	else:
		logger.info(f"Game {slot.slot_id} - {str(slot)} started!")
		msg = texts.match_is_nigh.format(slot.pubg_id)
		context.bot_data.setdefault('running_games', set()).add(slot)
	for player_id in slot.players:
		player_data = context.dispatcher.user_data.get(player_id)
		player_data['game_message'].delete()
		player_data['game_message'] = context.bot.send_message(player_id, msg)
		if not ready:
			player_data['balance'] = database.updateBalance(player_id, slot.bet)


def warnAdmins(context, slot_name):
	admins = database.getAdmins()
	for admin in admins:
		context.bot.send_message(
			admin['id'],
			texts.pubg_id_is_needed.format(slot_name),
			reply_markup=InlineKeyboardMarkup(
				buttons.createButton(texts.goto_admin, 'manage_matches'))
		)


def manageSlot(slot, context):
	logger.info(f"Slot {slot.slot_id} expired, players: {len(slot.players)}")
	ready = slot.ready
	if ready:
		warnAdmins(context, str(slot))
		context.job_queue.run_once(
			startGame, slot.time - timedelta(minutes=5), context=slot)
	for player_id in slot.players:
		player_data = context.dispatcher.user_data.get(player_id)
		if not ready:
			player_data['balance'] = database.updateBalance(player_id, slot.bet)
			msg = texts.match_didnt_happen.format(str(slot))
		else:
			msg = texts.match_starts_soon.format(str(slot))
		player_data['game_message'] = context.bot.send_message(player_id, msg)
		player_data['picked_slots'].discard(slot)


def checkSlots(context):
	now = datetime.now()
	slots = context.bot_data.setdefault('slots', [])
	for index, slot in enumerate(slots):
		if slot.full or slot.time <= now + timedelta(minutes=20):
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


def checkGames(context):
	running_games = context.bot_data.get('running_games', [])
	for game in running_games:
		if game.done:
			for player_id in game.players:
				player_data = context.dispatcher.user_data.get(player_id)
				player_data.pop('game_message').delete()
			winners = game.reward()
			for winner_id, place, prize in winners:
				winner_data = context.dispatcher.user_data.get(winner_id)
				winner_data['balance'] = database.updateBalance(winner_id, game.bet)
				winner_data['game_message'] = context.bot.send_message(
					winner_id, texts.victory.format(str(game), place, prize)
				)
			running_games.discard(game)
			logger.info(f"Game ended, winners are: {winners}")


def scheduleJobs(job_queue):
	job_queue.run_repeating(checkSlots, timedelta(minutes=5), first=0)
	job_queue.run_repeating(checkGames, timedelta(minutes=7), first=0)
	logger.info("Jobs scheduled")
