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
		self.players = set()
		self.paying_players = set()
		self.chat_id = None
		self.game_id = None
		self.slot_id = Slot.slots_count
		Slot.slots_count += 1

		logger.info(f"New slot ({self.time_string}) has been created")

	def __str__(self):
		return "{time} - {players} - {mode} - {view} - {bet}".format(
			time=self.time_string,
			players=len(self.players),
			mode=self.settings['mode'],
			view=self.settings['view'],
			bet=self.settings['bet']
		)

	def createButton(self, leave=False):
		if leave:
			button_text = f"{self.time_string} - {texts.leave_match}"
		elif not self.players:
			button_text = f"{self.time_string} - {texts.free_slot}"
		elif self.full():
			button_text = f"{self.time_string} - {texts.full_slot}"
		else:
			button_text = str(self)
		return buttons.createButton(button_text, f'slot_{self.slot_id}')

	def join(self, user_id):
		self.players.add(int(user_id))

	def paid(self, user_id):
		self.paying_players.add(int(user_id))

	def leave(self, user_id):
		self.players.discard(int(user_id))
		if not self.players:
			self.settings = dict.fromkeys(['mode', 'view', 'bet'], None)

	def full(self):
		return len(self.players) >= 70

	def ready(self):
		return len(self.paying_players) >= 50

	def isSet(self):
		return all(self.settings.values())

	def done(self):
		# pubg request
		pass

	def payout(self):
		# pubg request
		winners = set()  # of tuples (winner_id, place, prize)
		return winners
