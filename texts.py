# main menu
menu = {
	'msg': "Привет!",
	'next': {
		'admin': {
			'btn': "Управление",
		},
		'matches': {
			'btn': "График матчей",
		},
		'rooms': {
			'btn': "Горячая комната",
		},
		'profile': {
			'btn': "Личный кабинет",
		},
		'how': {
			'btn': "Как это работает?",
			'msg': "Как-то работает",
			'next': {
				'points': {
					'btn': "Правила начисления очков",
					'msg': "Как-то начисляются"
				},
				'service': {
					'btn': "Правила работы с сервисом",
					'msg': "Какие-то правила",
				},
				'faq': {
					'btn': "FAQ",
					'msg': "Вопросы и ответы",
				},
			},
		},
		'about': {
			'btn': "О нас",
			'msg': "О нас",
		}
	}
}

# matches
matches = {
	'msg': (
		"*Режим*: {mode}\n"
		"*Вид*: {view}\n"
		"*Ставка*: {bet}\n\n"
		"*Выбранный матч*: {match}"
	),
	'default': "все",
	'next': {
		'reset': {
			'btn': "Сбросить выбор"
		},
		'choose_match': {
			'btn': "Выбрать матч",
			'msg': "Найдено матчей: {}",
			'next': {}
		},
		'mode': {
			'btn': "Выбрать режим",
			'msg': "Выберите *РЕЖИМ* игры",
			'next': {
				'solo': {
					'btn': "SOLO"
				},
				'dual': {
					'btn': "DUAL"
				},
				'squad': {
					'btn': "SQUAD"
				},
				'payload': {
					'btn': "Payload"
				},
				'zombie': {
					'btn': "Zombie"
				},
			},
		},
		'view': {
			'btn': "Выбрать обзор",
			'msg': "Выберите *ОБЗОР* игры",
			'next': {
				'1st': {
					'btn': "От 1-го лица"
				},
				'3rd': {
					'btn': "От 3-го лица"
				},
			},
		},
		'bet': {
			'btn': "Выбрать ставку",
			'msg': "Выберите *СТАВКУ*",
			'next': {
				'30': {
					'btn': "30"
				},
				'60': {
					'btn': "60"
				},
				'90': {
					'btn': "90"
				},
			}
		},
	}
}
menu['next']['matches'].update(matches)
pubg_id_not_set = {
	'msg': "Сначала надо установить свой PUBG ID в профиле",
	'depth': 1,
	'next': {
		'profile': {
			'btn': "Личный кабинет",
		},
	}
}
match_is_chosen =\
	"Матч {} выбран. За 15 минут до начала потребуется подверждение готовности."

# rooms
rooms = {
	'msg': "Горячая комната",
	'next': {
		'battle_chat': {
			'btn': "Перейти в боевой чат"
		},
		'hot_rooms': {
			'btn': "Горячие комнаты",
			'msg': "Какой-то список здесь",
		},
	}
}
menu['next']['rooms'].update(rooms)

# profile
profile = {
	'msg': (
		"*КАБИНЕТ*\n\n"
		"PUBG ID: {}\n"
	),
	'next': {
		'add_funds': {
			'btn': "Пополнить баланс",
			'msg': "Укажите сумму пополнения",
		},
		'withdraw_funds': {
			'btn': "Вывести средства",
			'msg': "Укажите сумму вывода",
		},
		'set_pubg_id': {
			'btn': "Установить PUBG ID",
			'msg': "Введите PUBG ID",
		},
	}
}
menu['next']['profile'].update(profile)

# admin
admin = {
	'msg': "Администрирование",
	'next': {
		'spam': {
			'btn': "Отправить сообщения пользователям",
			'msg': "Здесь рассылка",
		},
		'admins': {
			'btn': "Управление администраторами",
			'msg': "Здесь управление админами",
		},
		'servers': {
			'btn': "Управление серверами",
			'msg': "Здесь управление cерверами",
		},
		'pubg_api': {
			'btn': "Управление API PUBG",
			'msg': "Здесь управление PUBG API",
		},
	}
}
menu['next']['admin'].update(admin)

# misc
error = "Ошибка. Попробуйте заново"
back = "Назад"
main = "В главное меню"
