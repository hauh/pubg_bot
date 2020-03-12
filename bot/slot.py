from logging import getLogger

from telegram import InlineKeyboardButton

import texts
import database

##############################

logger = getLogger(__name__)


class Slot:
	slots_count = 0

	def __init__(self, time):
		self.time = time
		self.time_string = time.strftime("%H:%M")
		self.settings = dict.fromkeys(['mode', 'view', 'bet'], None)
		self.players = set()
		self.winners = dict.fromkeys(range(1, 11))
		self.pubg_id = None
		self.is_finished = False

		Slot.slots_count += 1
		self.slot_id = Slot.slots_count

		logger.info(f"New slot ({self.time_string}) has been created")

	def __str__(self):
		return "{time} - {players} - {mode} - {view} - {bet}".format(
			time=self.time_string,
			players=len(self.players),
			mode=self.settings['mode'],
			view=self.settings['view'],
			bet=self.settings['bet']
		)

	@property
	def bet(self):
		return int(self.settings['bet'])

	@property
	def is_full(self):
		return len(self.players) >= 100

	@property
	def is_ready(self):
		return len(self.players) >= 70

	@property
	def is_set(self):
		return all(self.settings.values())

	def create_button(self, leave=False):
		if leave:
			text = f"{self.time_string} - {texts.leave_match}"
		elif not self.players:
			text = f"{self.time_string} - {texts.free_slot}"
		elif self.is_full:
			text = f"{self.time_string} - {texts.is_full_slot}"
		else:
			text = str(self)
		return [InlineKeyboardButton(text, callback_data=f'slot_{self.slot_id}')]

	def join(self, user_id):
		self.players.add(int(user_id))

	def leave(self, user_id):
		self.players.discard(int(user_id))
		if not self.players:
			self.settings = dict.fromkeys(['mode', 'view', 'bet'], None)

	def reward(self):
		winners = set()  # of tuples (winner_id, place, prize)
		total_sum = int(self.settings['bet']) * len(self.players)
		for place, username in self.winners:
			user = database.getUser(pubg_username=username)
			NotImplemented
		return winners
