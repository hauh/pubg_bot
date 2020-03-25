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
		self.settings = dict.fromkeys(['type', 'mode', 'view', 'bet'], None)
		self.players = set()
		self.winners = dict.fromkeys(range(1, 11))
		self.pubg_id = None
		self.room_pass = None

		Slot.slots_count += 1
		self.slot_id = Slot.slots_count

		logger.info(
			"New slot id: {id} [{time}] has been created".format(
				id=self.slot_id,
				time=self.time.strftime("%H:%M")
			)
		)

	def __str__(self):
		return "{time} - 👥{players} - {type} - {mode} - {view} - {bet}".format(
			time=self.time.strftime("%H:%M"),
			players=len(self.players),
			type=self.settings['type'],
			mode=self.settings['mode'],
			view=self.settings['view'],
			bet=self.settings['bet']
		)

	@property
	def bet(self):
		return int(self.settings['bet'])

	@property
	def is_full(self):
		return len(self.players) >= 90

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
			self.settings = dict.fromkeys(['type', 'mode', 'view', 'bet'], None)

	def reward(self):
		winners = set()
		prize_structure = config.prize_structure[self.game_type]
		prize_fund = self.prize_fund
		total_kills = 0
		for _, kills in self.winners.values():
			total_kills += kills
		kill_price = round(prize_fund / 100.0 * prize_structure['kill'] / total_kills)
		total_payout = 0
		for place, winner in self.winners.items():
			username, kills = winner
			if username != texts.user_not_found:
				percent = prize_structure[place]
				prize = round(prize_fund / 100.0 * percent) + kills * kill_price
				total_payout += prize
				user = database.getUser(pubg_username=username)
				winners.add((user['id'], place, prize))
		return winners, total_payout
