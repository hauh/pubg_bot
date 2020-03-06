from logging import getLogger
from datetime import datetime, timedelta

import texts
from slot import Slot

###############

logger = getLogger(__name__)


def startMatch(slot):
	logger.info(f"Slot {slot.slot_id} expired, users: {len(slot.players)}")
	pass


def checkSlots(context):
	now = datetime.now()
	slots = context.bot_data.setdefault('slots', [])
	for index, slot in enumerate(slots):
		if slot.full() or slot.time < now:
			ready_slot = slots.pop(index)
			if ready_slot.time + timedelta(minutes=30) < now:
				slots.insert(index, Slot(ready_slot.time))
			startMatch(ready_slot)
		elif slot.time < now:
			startMatch(slots.pop(index))
	if slots:
		next_slot_time = slots[-1].time
	else:
		next_slot_time = now.replace(minute=0 if now.minute < 30 else 30, second=0)
	while len(slots) < 24:
		next_slot_time += timedelta(minutes=30)
		slots.append(Slot(next_slot_time))


def scheduleJobs(job_queue):
	job_queue.run_repeating(checkSlots, timedelta(minutes=5), first=0)
	logger.info("Jobs scheduled")
