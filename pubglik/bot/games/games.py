"""Game classes for running games in slots"""

from pubglik.config import prizes as PRIZES


def factory(game_type, bet, players):
	if game_type == 'survival_easy':
		return SurvivalEasy(players, bet)
	if game_type == 'survival_medium':
		return SurvivalMedium(players, bet)
	if game_type == 'survival_hard':
		return SurvivalHard(players, bet)
	if game_type == 'kills':
		return Kills(players, bet)
	if game_type == 'mixed':
		return Mixed(players, bet)
	raise ValueError('undefined type')


class Game:
	"""Base class for all game types"""

	def __init__(self, players, bet):
		self.players = players
		self.bet = bet

	@property
	def winners_are_set(self):
		raise NotImplementedError()


class SurvivalType(Game):
	"""Base class for survival-type games"""

	def __init__(self, players, bet, **kwargs):
		super().__init__(players, bet)
		self.places = dict()
		start = 1
		for top, coef in kwargs['places'].items():
			self.places.update(dict.fromkeys(range(start, top + 1), coef))
			start = top + 1

	@property
	def winners_are_set(self):
		return not self.places

	def set_player_place(self, user_id, place):
		if not (player := self.players.get(user_id)):
			raise ValueError('unknown_player')
		if 'place' in player:
			raise ValueError('duplicate_player')
		try:
			place_coef = self.places.pop(place)
		except KeyError:
			raise ValueError('invalid_value')
		player['place'] = place
		player['prize']['for_place'] = self.bet * place * place_coef


class KillsType(Game):
	"""Base class for kills-type games"""

	def __init__(self, players, bet, **kwarg):
		super().__init__(players, bet)
		self.kill_coef = kwarg['kill_coef']
		self.kills = 0

	@property
	def winners_are_set(self):
		return self.kills == len(self.players) - 1

	def set_player_kills(self, user_id, kills):
		if not (player := self.players.get(user_id)):
			raise ValueError('unknown_player')
		if 'kills' in player:
			raise ValueError('duplicate_player')
		self.kills -= kills
		if kills < 0 or self.kills < 0:
			raise ValueError('invalid_value')
		player['kills'] = kills * self.kill_coef


class SurvivalEasy(SurvivalType):
	def __init__(self, players, bet):
		super().__init__(players, bet, places=PRIZES['survival_easy']['top'])


class SurvivalMedium(SurvivalType):
	def __init__(self, players, bet):
		super().__init__(players, bet, places=PRIZES['survival_medium']['top'])


class SurvivalHard(SurvivalType):
	def __init__(self, players, bet):
		super().__init__(players, bet, places=PRIZES['survival_hard']['top'])


class Kills(KillsType):
	def __init__(self, players, bet):
		super().__init__(players, bet, kill_coef=PRIZES['kills']['kill'])


class Mixed(SurvivalType, KillsType):
	"""Mixed survival/kills game"""

	def __init__(self, players, bet):
		super().__init__(
			players, bet,
			kill_coef=PRIZES['mixed']['kill'],
			places=PRIZES['mixed']['top']
		)

	@property
	def winners_are_set(self):
		return not self.players and self.kills == len(self.players) - 1
