"""Slot class collects players, stores game info and distributes rewards"""

from pubglik import database
from pubglik.config import enough_players as ENOUGH_PLAYERS
from pubglik.config import max_players as MAX_PLAYERS
from pubglik.interface.texts import settings_names, short_names

from . import games

##############################

SETTINGS = ['type', 'mode', 'view', 'bet']


class Slot:
	"""
	Slot instantiated with a specifict datetime.time (game start time).	Slot
	stores and updates database with joined or left players, game settings,
	game room id and password, and prizes, which Slot can calculate for every
	player and yield.
	"""

	def __init__(self, time, **kwargs):
		self.slot_id = kwargs.get('id') or database.create_slot(time)
		self.time = time
		self.settings = {key: kwargs.get(key) for key in SETTINGS}
		self.pubg_id = kwargs.get('pubg_id')
		self.room_pass = kwargs.get('room_pass')
		self.players = dict()
		self.game = None
		self.is_finished = False

	def __str__(self):
		return (
			"🕑{time}👥{players}🎮{type}, {mode}👁{view}💲{bet}".format(
				time=self.time.strftime('%H:%M'),
				players=len(self.players),
				type="---" if not (_type := self.settings['type'])
					else short_names.get(_type) or settings_names.get(_type),
				mode=settings_names.get(self.settings['mode'], "---"),
				view=self.settings['view'] or "---",
				bet=self.settings['bet'] or "---"
			)
		)

	@property
	def bet(self):
		return self.settings['bet']

	@property
	def is_full(self):
		return len(self.players) >= MAX_PLAYERS

	@property
	def is_ready(self):
		return len(self.players) >= ENOUGH_PLAYERS

	@property
	def is_set(self):
		return all(self.settings.values())

	@property
	def is_room_set(self):
		return self.pubg_id and self.room_pass

	@property
	def is_running(self):
		return bool(self.game)

	@property
	def prize_fund(self):
		return len(self.players) * self.bet

	def join(self, user_id):
		database.join_slot(self.slot_id, user_id, self.bet)
		self.players[user_id] = dict()

	def leave(self, user_id):
		database.leave_slot(self.slot_id, user_id)
		del self.players[user_id]

	def update_settings(self, settings):
		settings['bet'] = int(settings['bet'])
		database.update_slot(self.slot_id, **settings)
		self.settings.update(settings)

	def reset_settings(self):
		self.settings = dict.fromkeys(SETTINGS, None)
		database.update_slot(self.slot_id, **self.settings)

	def run_game(self, pubg_id, room_pass):
		pubg_id = int(pubg_id)
		database.update_slot(self.slot_id, pubg_id=pubg_id, room_pass=room_pass)
		self.pubg_id = pubg_id
		self.room_pass = room_pass
		self.game = games.factory(self.settings, self.bet, self.players)

	def reset_results(self):
		for results in self.players.values():
			results.clear()
		self.game = games.factory(self.settings, self.players)

	def reward(self):
		for user_id, result in self.players.items():
			if prizes := result.get('prize'):
				if place := result.get('place', 0):
					database.set_player_result(
						self.slot_id, user_id, 'place', place)
				if kills := result.get('kills', 0):
					database.set_player_result(
						self.slot_id, user_id, 'kills', kills)
				prize = prizes.get('for_place', 0) + prizes.get('for_kills', 0)
				database.change_balance(
					user_id, prize, 'prize', slot_id=self.slot_id)
				yield (user_id, prize, place, kills)
		database.update_slot(self.slot_id, finished=True)

	def delete(self):
		database.delete_slot(self.slot_id)
