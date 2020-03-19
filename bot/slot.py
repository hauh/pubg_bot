from logging import getLogger

from telegram import InlineKeyboardButton

import config
import texts
import database

##############################

logger = getLogger(__name__)


class Slot:
	slots_count = 0

	def __init__(self, time):
		self.time = time
		self.settings = dict.fromkeys(['mode', 'view', 'bet', 'type'], None)
		self.settings['type'] = 'survival'
		self.players = set()
		self.winners = dict.fromkeys(range(1, 3))
		self.pubg_id = None

		Slot.slots_count += 1
		self.slot_id = Slot.slots_count

		logger.info(f"New slot ({str(self)}) has been created")

	def __str__(self):
		return "{time} - {players} - {mode} - {view} - {bet} - {type}".format(
			time=self.time.strftime("%H:%M"),
			players=len(self.players),
			mode=self.settings['mode'],
			view=self.settings['view'],
			bet=self.settings['bet'],
			type=self.settings['type']
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

	@property
	def prize_fund(self):
		return int(self.settings['bet']) * len(self.players)

	@property
	def game_type(self):
		return self.settings['type']

	def switch_game_type(self):
		if self.settings['type'] == 'survival':
			self.settings['type'] = 'kills'
		else:
			self.settings['type'] = 'survival'

	def create_button(self, leave=False):
		if leave:
			text = f"{self.time.strftime('%H:%M')} - {texts.leave_match}"
		elif not self.players:
			text = f"{self.time.strftime('%H:%M')} - {texts.free_slot}"
		elif self.is_full:
			text = f"{self.time.strftime('%H:%M')} - {texts.full_slot}"
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
		winners = set()
		prize_structure = config.prize_structure[self.game_type]
		prize_fund = self.prize_fund
		total_payout = 0
		for place, winner in self.winners.items():
			username, kills = winner
			if username != texts.user_not_found:
				percent = prize_structure[place]
				prize = round(prize_fund / 100.0 * percent) + kills * prize_structure['kill']
				total_payout += prize
				user = database.getUser(pubg_username=username)
				winners.add((user['id'], place, prize))
		return winners, total_payout
