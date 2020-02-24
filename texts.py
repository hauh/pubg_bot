# main menu
menu = {
	'msg': "Привет!"
}
menu['next'] = {
	'matches': {
		'btn': "График матчей",
		'msg': "Список матчей здесь",
	},
	'room': {
		'btn': "Горячая комната",
		'msg': "Горячая комната",
	},
	'profile': {
		'btn': "Личный кабинет",
		'msg': (
			"**КАБИНЕТ**\n\n"
			"PUBG ID: {}\n"
			"Статистика в боте {}"
		)
	},
	'how': {
		'btn': "Как это работает?",
		'msg': "Как-то работает",
	},
	'about': {
		'btn': "О нас",
		'msg': "О нас",
	}
}

# matches
menu['next']['matches']['next'] = {
	'mode': {
		'msg': "Выберите **РЕЖИМ** игры",
		'btn': "Выбрать режим",
	},
	'view': {
		'msg': "Выберите **ОБЗОР** игры",
		'btn': "Выбрать обзор",
	},
	'bet': {
		'msg': "Выберите **СТАВКУ**",
		'btn': "Выбрать ставку",
	},
}
menu['next']['matches']['next']['mode']['next'] = {
	'solo': {
		'btn': "SOLO"
	},
	'dual': {
		'btn': "DUAL"
	},
	'squad': {
		'btn': "SQUAD"
	},
}
menu['next']['matches']['next']['view']['next'] = {
	'1st': {
		'btn': "От 1-го лица"
	},
	'3rd': {
		'btn': "От 3-го лица"
	},
}
menu['next']['matches']['next']['bet']['next'] = {
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

# room
menu['next']['room']['next'] = {
	'battle_chat': {
		'btn': "Боевой чат"
	},
	'hot_rooms': {
		'btn': "Горячие комнаты",
		'msg': "Какой-то список здесь",
	},
}

# profile
menu['next']['profile']['next'] = {
	'top_up': {
		'btn': "Пополнить баланс",
		'msg': "Укажите сумму пополнения",
	},
	'payout': {
		'btn': "Вывести средства",
		'msg': "Укажите сумму вывода",
	},
	'set_pubdg_id': {
		'btn': "Установить PUBG ID",
		'msg': "Введите PUBG ID",
	},
}

# how
menu['next']['how']['next'] = {
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
}

# admin
admin_option = {
	'admin': {
		'btn': "Управление",
	}
}
admin = {
	'msg': "Администрирование",
	'next'		: {
		'spam': {
			'btn'	: "Отправить сообщения пользователям",
			'msg'	: "Здесь рассылка",
			'next'	: {
			}
		},
		'admins': {
			'btn'	: "Управление администраторами",
			'msg'	: "Здесь управление админами",
			'next'	: {
			}
		},
		'servers': {
			'btn'	: "Управление серверами",
			'msg'	: "Здесь управление cерверами",
			'next'	: {
			}
		},
		'pubg_api': {
			'btn'	: "Управление API PUBG",
			'msg'	: "Здесь управление PUBG API",
			'next'	: {
			}
		},
	}
}

# misc
error = "Ошибка"
back = "Назад"
main = "В главное меню"
