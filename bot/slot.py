from logging import getLogger

from telegram import InlineKeyboardButton

import config
import texts
import database

##############################

logger = getLogger(__name__)


class Slot:
	def __init__(self, time):
		self.time = time
		self.settings = dict.fromkeys(['type', 'mode', 'view', 'bet'], None)
		self.players = set()
		self.winners = dict.fromkeys(range(1, 11))
		self.killers = dict()
		self.pubg_id = None
		self.room_pass = None
		self.slot_id = None

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
	def players_count(self):
		return len(self.players)

	@property
	def is_full(self):
		return len(self.players) >= config.max_players

	@property
	def is_ready(self):
		return len(self.players) >= config.enough_players

	@property
	def is_set(self):
		return all(self.settings.values())

	@property
	def prize_fund(self):
		return int(self.settings['bet']) * self.players_count

	@property
	def game_type(self):
		return self.settings['type']

	@property
	def total_kills(self):
		return sum(self.killers.values())


	@property
	def winners_are_set(self):
		return (
			(self.game_type == 'survival' and all(self.winners.values()))
			or (self.game_type == 'kills' and self.total_kills == self.players_count - 1)
			or (self.game_type == 'mixed' and all(self.winners.values())
				and self.total_kills == self.players_count - 1)
		)

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
		if self.total_kills:
			kill_price = round(prize_fund / 100.0 * prize_structure['kill'] / self.total_kills)
		else:
			kill_price = 0
		total_payout = 0
		if self.game_type != 'kills':
			for place, winner in self.winners.items():
				if winner != texts.user_not_found:
					percent = prize_structure[place]
					kills = self.killers.pop(winner, 0)
					prize = round(prize_fund / 100.0 * percent) + kills * kill_price
					total_payout += prize
					user = database.getUser(pubg_username=winner)
					victory_message = texts.winner_place.format(place)
					if kills:
						victory_message += texts.kills_count.format(kills)
					winners.add((user['id'], victory_message, prize))
		if self.game_type != 'survival':
			for killer, kills in self.killers.items():
				prize = kills * kill_price
				total_payout += prize
				user = database.getUser(pubg_username=killer)
				winners.add((user['id'], texts.kills_count.format(kills), prize))
		return winners, total_payout
