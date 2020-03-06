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
		"Выберите до трёх матчей, в которых хотите участвовать\n\n"
		"*Выбранные матчи*:\n{}"
	),
	'default': "Не выбраны",
	'next': {
		'slot_': {
			'msg': (
				"Cоздание слота\n\n"
				"*Режим*: {mode}\n"
				"*Обзор*: {view}\n"
				"*Ставка*: {bet}"
			),
			'default': "не выбрано",
			'next': {
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
		},
	},
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
free_slot = "Создать матч"
full_slot = "Слот заполнен"
match_already_created = "Слот уже был кем-то создан"
maximum_matches = "Вы уже записаны на три матча"
left_from_match = "Вы вышли из этого матча"
match_not_found = "Матч не найден. Вероятно, он уже начался или завершился."
match_is_chosen = "Матч выбран. За 15 минут до начала потребуется подтвердить."
leave_match = "Выйти"

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
		"*ЛИЧНЫЙ КАБИНЕТ*\n\n"
		"*Telegram ID*: {}\n"
		"*PUBG ID*: {}\n"
		"*Баланс*: {}\n"
	),
	'next': {
		'balance_history': {
			'btn': "Посмотреть историю операций",
			'msg': "Операций не найдено",
			'next': {}
		},
		'add_funds': {
			'btn': "Пополнить баланс",
			'msg': "Введите сумму пополнения",
			'input': {
				'msg_valid': "Сумма *пополнения*: {}",
				'msg_error': "Невалидное значение",
			}
		},
		'withdraw_funds': {
			'btn': "Вывести средства",
			'msg': "Ввведите сумму вывода",
			'input': {
				'msg_valid': "Сумма *вывода*: {}",
				'msg_error': "Невалидное значение",
			}
		},
		'set_pubg_id': {
			'btn': "Установить PUBG ID",
			'msg': "Введите PUBG ID",
			'input': {
				'msg_valid': "Новый PUBG ID: {}",
				'msg_error': "ID не найден",
			}
		},
	}
}
menu['next']['profile'].update(profile)

funds_added = "Баланс пополнен"
insufficient_funds = "Недостаточно средств"
funds_withdrawn = "Сумма списана с баланса"
pubg_id_not_found = "Такой PUBG ID не найден"
pubg_id_is_set = "Новый PUBG ID установлен"

# admin
admin = {
	'msg': "Администрирование",
	'next': {
		'mailing': {
			'btn': "Отправить сообщения пользователям",
			'msg': "Здесь будет рассылка",
		},
		'manage_admins': {
			'btn': "Управление администраторами",
			'msg': "Управление администраторами",
			'next': {
				'add_admin': {
					'btn': "Добавить администратора",
					'msg': (
						"Введите юзернейм нового администратора. "
						"У него должен быть диалог с ботом"
					),
					'input': {
						'msg_valid': "Найден пользователь: @{}",
						'msg_error': "Такой пользователь не найден. Проверьте юзернейм",
					}
				},
				'remove_admin': {
					'btn': "Удалить администратора",
					'msg': "Администраторы:\n{}\nВыберите, кого удалить",
					'next': {}
				}
			}
		},
		'servers': {
			'btn': "Управление серверами",
			'msg': "Здесь управление cерверами",
			'next': {}
		},
		'pubg_api': {
			'btn': "Управление API PUBG",
			'msg': "Здесь управление PUBG API",
		},
	}
}
menu['next']['admin'].update(admin)
admin_added = "Администратор добавлен!"
admin_removed = "Администартор удалён!"
admin_update_failed = "Не получилось"

# misc
error = "Ошибка. Попробуйте заново"
back = "Назад"
main = "В главное меню"
confirm = "Подтвердить"
reset = "Сбросить выбор"
