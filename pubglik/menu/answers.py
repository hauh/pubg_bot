"""Callback query answers."""

from pubglik import config

##############################

answers = {
	# ########## admin ########## #
	'set_room': {
		'success': {
			'text': "ID комнаты и пароль сохранены.",
			'show_alert': False,
		}
	},
	'set_winners': {
		'success': {
			'text': "Начато распределение призов.",
			'show_alert': False
		}
	},
	'add_admin': {
		'success': {
			'text': "Администратор добавлен!",
			'show_alert': False
		}
	},
	'revoke_admin': {
		'success': {
			'text': "Администратор удалён!",
			'show_alert': False,
		}
	},
	'change_balance': {
		'success': {
			'text': "Баланс изменён.",
			'show_alert': False
		}
	},
	'ban_user': {
		'success': {
			'text': "Забанен!",
			'show_alert': False
		}
	},
	'unban_user': {
		'success': {
			'text': "Разбанен!",
			'show_alert': False
		}
	},
	'mailing': {
		'success': {
			'text': "Начата рассылка сообщений.",
			'show_alert': True,
		}
	},
	'debug_mode': {
		'debug_off': {
			'text': "Режим дебага теперь выключен.",
			'show_alert': False
		},
		'debug_on': {
			'text': "Режим дебага теперь ВКЛЮЧЕН!",
			'show_alert': True
		},
	},

	# ########## tournaments ########## #
	'tournaments': {
		'pubg_required': {
			'text': (
				"Привет, Игрок! "
				"Для начала пройди регистрацию - вкладка «Личный Кабинет».",
			),
			'show_alert': True
		}
	},
	'slot': {
		'not_found': {
			'text': "Турнир не найден. Вероятно, он уже начался или завершился.",
			'show_alert': False,
		},
		'maximum': {
			'text': "Вы уже записаны на три турнира.",
			'show_alert': True,
		},
		'expensive': {
			'text': "У вас не хватает средств для участия в этом турнире.",
			'show_alert': True,
		},
		'full': {
			'text': "Турнир заполнен.",
			'show_alert': True,
		},
		'already_set': {
			'text': "Турнир уже был кем-то создан.",
			'show_alert': True,
		},
		'too_late': {
			'text': "Нельзя выйти: турнир уже готовится к началу.",
			'show_alert': True,
		},
		'left': {
			'text': "Вы вышли из турнира. Ставка возвращена на ваш счёт.",
			'show_alert': True,
		},
		'joined': {
			'text': (
				f"Турнир выбран. За {config.times['send_room']} мин. "
				"до начала придёт пароль от комнаты."
			),
			'show_alert': True
		},
	},

	# ########## cabinet ########## #
	'set_pubg_username': {
		'success': {
			'text': "Новый ник PUBG установлен.",
			'show_alert': False
		},
		'duplicate': {
			'text': "Такой ник уже зарегистрирован.",
			'show_alert': True
		},
	},
	'set_pubg_id': {
		'success': {
			'text': "Новый PUBG ID установлен.",
			'show_alert': False
		},
		'duplicate': {
			'text': "Такой PUBG ID уже зарегистрирован.",
			'show_alert': True
		},
	},
	'withdraw_money': {
		'too_much': {
			'text': "На вашем счету недостаточно средств.",
			'show_alert': True
		},
		'error': {
			'text': "Произошла ошибка, попробуйте позже или обратитесь в поддержку.",
			'show_alert': True
		},
	},
	'amount': {
		'too_much': {
			'text': "На вашем счету недостаточно средств.",
			'show_alert': True
		},
	}
}
