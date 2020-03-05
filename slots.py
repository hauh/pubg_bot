from logging import getLogger

import texts
import buttons

##############################

logger = getLogger(__name__)


class Slot:
	slots_count = 0

	def __init__(self, time):
		self.time = time
		self.time_string = time.strftime("%H:%M")
		self.settings = dict.fromkeys(['mode', 'view', 'bet'], None)
		self.user_count = 0
		self.chat_id = None
		self.game_id = None
		self.slot_id = Slot.slots_count
		Slot.slots_count += 1

		logger.info(f"New slot ({self.time_string}) created")

	def createButton(self, leave=False):
		if leave:
			button_text = f"{self.time_string} - {texts.leave_match}"
		elif self.user_count == 0:
			button_text = f"{self.time_string} - {texts.free_slot}"
		elif self.full():
			button_text = f"{self.time_string} - {texts.full_slot}"
		else:
			button_text = str(self)
		return buttons.createButton(button_text, f'slot_{self.slot_id}')

	def full(self):
		return self.user_count == 70

	def leave(self):
		self.user_count -= 1
		if self.user_count <= 0:
			self.user_count = 0
			self.settings = dict.fromkeys(['mode', 'view', 'bet'], None)

	def __str__(self):
		return "{time} - {users} - {mode} - {view} - {bet}".format(
			time=self.time_string,
			users=self.user_count,
			mode=self.settings['mode'],
			view=self.settings['view'],
			bet=self.settings['bet']
		)
