"""Misc texts."""

from pubglik import config

##############################

error = "Ошибка. Попробуйте заново"

# settings
settings_names = {
	'survival_easy': "Выживание (лёгкий)",
	'survival_medium': "Выживание (средний)",
	'survival_hard': "Выживание (тяжёлый)",
	'kills': "Убийства",
	"mixed": "Смешанный",
	'1st': "От первого лица",
	'3rd': "От третьего лица",
	'solo': "SOLO",
	'dual': "DUAL",
	'squad': "SQUAD",
	'payload': "Payload",
	'zombie': "Zombie",
}
short_names = {
	'survival_easy': "Выж(лёгк)",
	'survival_medium': "Выж(ср)",
	'survival_hard': "Выж(тяж)",
}

# games
slot_is_ready = {
	'admins': "Турнир [{}] собрался. Введите ID комнаты и пароль в админке.",
	'users': (
		"Турнир [{}] собрался! "
		f"*За {config.times['send_room']} мин.* "
		"до начала вы получите сообщение с именем комнаты и паролем."
	)
}
game_is_starting = {
	'admins': "Турнир [{}] (PUBG ID {}) начался!",
	'users': (
		"Ваш турнир [{}] "
		f"*начнётся в течение {config.times['send_room']} мин*.\n"
		"Имя комнаты: *{}*, пароль: *{}*"
	)
}
game_ended = {
	'admins': (
		"Турнир [{game}] ({pubg_id}) завершён.\n"
		"Всего *ставок: {total_bets}*, призовых *выплачено: {prizes}*"
	),
	'users': (
		"Турнир [{game}] завершён, ваш результат:\n{place}{kills}\n"
		"Ваш счёт пополнен на *{prize}*. Поздравляем!"
	)
}
winner_place = "Вы заняли *место: {}*\n"
kills_count = "Вы совершили *убийств: {}*\n"
game_didnt_happen = "Турнир [{}] не состоялся. Ставка возвращена на ваш счёт."
game_failed = "Турнир [{}] отменён - не создана комната!"

# webserver
game_not_set = "Ещё не выбрано!"
got_money = "Поступил платёж на сумму {}. Ваш баланс: {}."
