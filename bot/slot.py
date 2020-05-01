import config
import database

##############################


class Slot:
	def __init__(self, time):
		self.slot_id = database.create_slot(time)
		self.time = time
		self.settings = dict.fromkeys(['type', 'mode', 'view', 'bet'], None)
		self.players = dict()
		self.prize_fund = 0
		self.started = self.finished = False
		self.pubg_id = self.room_pass = None

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
		return self.settings['bet']

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
	def is_room_set(self):
		return self.pubg_id and self.room_pass

	@property
	def game_type(self):
		return self.settings['type']

	@property
	def prize_structure(self):
		return config.prize_structure[self.game_type]

	@property
	def total_kills(self):
		return sum(player.get('kills', 0) for player in self.players.values())

	@property
	def winners_are_set(self):
		if (0 < sum(self.places_to_reward())
		!= sum([player.get('place', 0) for player in self.players.values()])):
			return False
		if (self.prize_structure['kills']
		and self.total_kills != self.players_count - 1):
			return False
		return True

	def reset_results(self):
		for results in self.players.values():
			results.clear()

	def update_settings(self, settings):
		database.update_slot(self.slot_id, **settings)
		settings['bet'] = int(settings['bet'])
		self.settings.update(settings)

	def places_to_reward(self):
		return set(self.prize_structure.keys()) - set(['kills'])

	def join(self, user_id):
		database.join_slot(self.slot_id, user_id, self.bet)
		self.players[user_id] = dict()
		self.prize_fund += self.bet

	def leave(self, user_id):
		database.leave_slot(self.slot_id, user_id)
		del self.players[user_id]
		self.prize_fund -= self.bet
		if not self.players:
			self.settings = dict.fromkeys(['type', 'mode', 'view', 'bet'], None)

	def update_room(self, pubg_id, room_pass):
		pubg_id = int(pubg_id)
		database.update_slot(self.slot_id, pubg_id=pubg_id, room_pass=room_pass)
		self.pubg_id = pubg_id
		self.room_pass = room_pass

	def distribute_prizes(self):
		total_payout = 0
		if self.prize_structure['kills'] and self.total_kills:
			kill_price = round(
				self.prize_fund / 100.0
				* prize_structure['kills']
				/ self.total_kills
			)
		else:
			kill_price = 0
		for player_results in self.players.values():
			if place := player_results.get('place'):
				prize = round(
					self.prize_fund / 100.0
					* self.prize_structure[place]
				)
				player_results.setdefault('prize', {}).update(for_place=prize)
				total_payout += prize
			if kills := player_results.get('kills'):
				prize = kills * kill_price
				player_results.setdefault('prize', {}).update(for_kills=prize)
				total_payout += prize
		return total_payout

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
