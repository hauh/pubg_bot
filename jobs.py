from logging import getLogger
from datetime import datetime, timedelta

import texts
import database
from slot import Slot
from menu import MenuHandler

###############

logger = getLogger(__name__)


def startGame(context):
	pass


def manageSlot(slot, context):
	logger.info(f"Slot {slot.slot_id} expired, players: {len(slot.players)}")
	if slot.full():
		for player_id in slot.players:
			player_user_data = context.dispatcher.user_data.get(player_id, None)
			player_chat_data = context.dispatcher.chat_data.get(player_id, None)
			if not player_user_data or not player_chat_data:
				break
			message_text = texts.match_info.format(
				game=str(slot),
				balance=player['balance'],
				bet=slot.settings['bet']
			)
			if player_user_data['balance'] < slot.settings['bet']:
				message_text += texts.too_expensive_match
			old_messages = player_chat_data.setdefault('old_messages', [])
			MenuHandler.cleanChat(old_messages)
			old_messages.append(
				context.bot.send_message(
					player_id, message_text,
					# reply_markup=texts.confirmation
				)
			)
			player_chat_data['history'] = 'confirmation'
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
		next_slot_time += timedelta(minutes=30)
		slots.append(Slot(next_slot_time))


def checkGames(context):
	# context.bot.send_message(190267791, "too easy")
	# print(context.dispatcher.chat_data)
	# print(context.dispatcher.user_data)
	pass


def scheduleJobs(job_queue):
	job_queue.run_repeating(checkSlots, timedelta(minutes=5), first=0)
	job_queue.run_repeating(checkGames, timedelta(seconds=9), first=0)
	logger.info("Jobs scheduled")
