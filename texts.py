# main menu
main_menu = {
	'msg': "Привет!",
	'depth': 0
}
main_menu['next'] = {
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
		'depth': 1
	},
	'about': {
		'btn': "О нас",
		'msg': "О нас",
		'depth': 1
	}
}
main_menu['extra'] = {
	'admin': {
		'btn': "Управление",
	}
}


# matches
matches = {
	'msg': (
		"*Режим*: {mode}\n"
		"*Вид*: {view}\n"
		"*Ставка*: {bet}\n\n"
		"*Найдено матчей*: {found}"
	),
	'default': "все",
	'depth': 1
}
matches['next'] = {
	'mode': {
		'btn': "Выбрать режим",
		'msg': "Выберите *РЕЖИМ* игры",
	},
	'view': {
		'btn': "Выбрать обзор",
		'msg': "Выберите *ОБЗОР* игры",
	},
	'bet': {
		'btn': "Выбрать ставку",
		'msg': "Выберите *СТАВКУ*",
	},
}
matches['extra'] = {
	'reset': {
		'btn': "Сбросить фильтры"
	}
}
matches['next']['mode']['next'] = {
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
matches['next']['view']['next'] = {
	'1st': {
		'btn': "От 1-го лица"
	},
	'3rd': {
		'btn': "От 3-го лица"
	},
}
matches['next']['bet']['next'] = {
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

# rooms
rooms = {
	'msg': "Горячая комната",
	'depth': 1
}
rooms['next'] = {
	'battle_chat': {
		'btn': "Перейти в боевой чат"
	},
	'hot_rooms': {
		'btn': "Горячие комнаты",
		'msg': "Какой-то список здесь",
	},
}

# profile
profile = {
	'msg': (
		"*КАБИНЕТ*\n\n"
		"PUBG ID: {}\n"
		"Статистика в боте {}"
	),
	'depth': 1
}
profile['next'] = {
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
main_menu['next']['how']['next'] = {
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
admin = {
	'msg': "Администрирование",
	'depth': 1
}
admin['next'] = {
	'spam': {
		'btn'	: "Отправить сообщения пользователям",
		'msg'	: "Здесь рассылка",
	},
	'admins': {
		'btn'	: "Управление администраторами",
		'msg'	: "Здесь управление админами",
	},
	'servers': {
		'btn'	: "Управление серверами",
		'msg'	: "Здесь управление cерверами",
	},
	'pubg_api': {
		'btn'	: "Управление API PUBG",
		'msg'	: "Здесь управление PUBG API",
	},
}

# misc
error = "Ошибка"
back = "Назад"
main = "В главное меню"
