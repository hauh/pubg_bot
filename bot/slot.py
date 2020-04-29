from telegram import InlineKeyboardButton

import config
import texts
import database

##############################


class Slot:
	def __init__(self, time):
		self.slot_id = database.create_slot(time)
		self.time = time
		self.settings = dict.fromkeys(['type', 'mode', 'view', 'bet'], None)
		self.players = set()
		self.winning_places = range(1, 11)
		self.is_running = False
		self.pubg_id = None
		self.room_pass = None
		self.reset_winners()

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
			(self.game_type == 'kills' and self.total_kills == self.players_count - 1)
			or (self.game_type == 'survival' and all(self.winners.values()))
			or (self.game_type == 'mixed' and all(self.winners.values())
				and self.total_kills == self.players_count - 1)
		)

	def reset_winners(self):
		self.winners = dict.fromkeys(self.winning_places)
		self.killers = dict()

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
		self.players.add(user_id)
		database.join_slot(self.slot_id, user_id, self.bet)

	def leave(self, user_id):
		self.players.discard(user_id)
		database.leave_slot(self.slot_id, user_id)
		if not self.players:
			self.settings = dict.fromkeys(['type', 'mode', 'view', 'bet'], None)

	def update_settings(self, settings):
		settings['bet'] = int(settings['bet'])
		self.settings.update(settings)
		database.update_slot(self.slot_id, **settings)

	def update_room(self, pubg_id, room_pass):
		pubg_id = int(pubg_id)
		self.pubg_id = pubg_id
		self.room_pass = room_pass
		database.update_slot(self.slot_id, pubg_id=pubg_id, room_pass=room_pass)

	def reward(self):
		winners = set()
		prize_structure = config.prize_structure[self.game_type]
		prize_fund = self.prize_fund
		if self.total_kills:
			kill_price = round(
				prize_fund / 100.0 * prize_structure['kill'] / self.total_kills)
		else:
			kill_price = 0
		total_payout = 0
		if self.game_type != 'kills':
			for place, winner in self.winners.items():
				if winner != texts.user_not_found:
					database.set_player_result(self.slot_id, winner, 'place', place)
					percent = prize_structure[place]
					kills = self.killers.pop(winner, 0)
					prize = round(prize_fund / 100.0 * percent) + kills * kill_price
					total_payout += prize
					user = database.get_user(pubg_username=winner)
					victory_message = texts.winner_place.format(place)
					if kills:
						victory_message += texts.kills_count.format(kills)
					winners.add((user['id'], victory_message, prize))
		if self.game_type != 'survival':
			for killer, kills in self.killers.items():
				database.set_player_result(self.slot_id, killer, 'kills', kills)
				prize = kills * kill_price
				total_payout += prize
				user = database.get_user(pubg_username=killer)
				winners.add((user['id'], texts.kills_count.format(kills), prize))
		database.update_slot(self.slot_id, finished=True)
		return winners, total_payout
