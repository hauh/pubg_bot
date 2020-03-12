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
		},
		'battle_chat': {
			'btn': "Общий чат"
		},
	}
}
game_awaits_payment = (
	"*У вас есть игра, котора начнётся в {}!\n"
	"Не забудьте внести ставку*"
)
game_starts_soon = "*Ваша игра начнётся в {}, её PUBG ID: {}*"

# matches
matches = {
	'msg': (
		"Выберите до трёх матчей, в которых хотите участвовать. "
		"Cтавка будет заморожена на вашем балансе "
		"пока матч не начнётся, или вы из него не выйдете "
		"(не позднее, чем за 20 минут до начала).\n"
		"*Ваш баланс*: {balance}\n"
		"*Выбранные матчи*:\n{matches}"
	),
	'default': "Не выбраны",
	'next': {
		'slot_': {
			'msg': (
				"Cоздание слота. "
				"Выбранная ставка будет списана с баланса после подтверждения.\n"
				"*Баланс*: {balance}\n"
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
pubg_is_not_set = "Сначала установите свой PUBG ник и ID в личном кабинете"
free_slot = "Создать матч"
full_slot = "Слот заполнен"
match_already_created = "Слот уже был кем-то создан"
maximum_matches = "Вы уже записаны на три матча"
left_from_match = "Вы вышли из матча. Ставка возвращена на баланс."
match_not_found = "Матч не найден. Вероятно, он уже начался или завершился."
match_didnt_happen = "Матч [{}] не состоялся. Ставка возвращена на ваш баланс."
match_is_chosen = "Матч выбран. За 5 минут до начала вы получите PUBG ID игры."
match_is_starting_soon = (
	"Матч [{}] начнётся через 20 минут! "
	"За пять минут до начала вы получите сообщение с PUBG ID игры."
)
match_is_nigh = "Ваш матч начнётся через 5 минут. PUBG ID игры:\n*{}*"
leave_match = "Выйти"

# profile
profile = {
	'msg': (
		"*ЛИЧНЫЙ КАБИНЕТ*\n\n"
		"*Telegram ID*: {user_id}\n"
		"*PUBG ник*: {pubg_id}\n"
		"*PUBG ID*: {pubg_username}\n"
		"*Баланс*: {balance}\n"
	),
	'next': {
		'set_pubg_username': {
			'btn': "Установить ник PUBG",
			'msg': "Введите ваш игровой ник",
			'input': {
				'msg_valid': "*Новый ник*: {}",
				'msg_error': "Слишком длинный ник",
				'msg_success': "Новый ник PUBG установлен",
				'msg_fail': "Неизвестная ошибка"
			}
		},
		'set_pubg_id': {
			'btn': "Установить ID PUBG",
			'msg': "Введите ваш игровой ID",
			'input': {
				'msg_valid': "*Новый PUBG ID*: {}",
				'msg_error': "ID должен состоять только из 8-10 цифр",
				'msg_success': "Новый PUBG ID установлен",
				'msg_fail': "Неизвестная ошибка"
			}
		},
		'add_funds': {
			'btn': "Пополнить баланс",
			'msg': "Введите сумму пополнения",
			'input': {
				'msg_valid': "Сумма *пополнения*: {}",
				'msg_error': "Введите число в диапазоне 10 - 99999",
				'msg_success': "Баланс пополнен",
				'msg_fail': "Неизвестная ошибка"
			}
		},
		'withdraw_funds': {
			'btn': "Вывести средства",
			'msg': "Ввведите сумму вывода",
			'input': {
				'msg_valid': "Сумма *вывода*: {}",
				'msg_error': "Введите число в диапазоне 10 - 99999",
				'msg_success': "Сумма списана с баланса",
				'msg_fail': "Недостаточно средств"
			}
		},
		'balance_history': {
			'btn': "Посмотреть историю операций",
			'msg': "Операций не найдено",
			'next': {}
		},
	}
}
menu['next']['profile'].update(profile)

funds_added = "Баланс пополнен"
insufficient_funds = "Недостаточно средств"
funds_withdrawn = "Сумма списана с баланса"
pubg_id_is_set = "Новый PUBG ID установлен"

# admin
admin = {
	'msg': "Администрирование",
	'next': {
		'manage_matches': {
			'btn': "Управление матчами",
			'msg': (
				"*Матчи, ожидающие начала*:\n{pending}\n"
				"*Матчи в процессе*:\n{running}"
			),
			'default': "нет",
			'next': {
				'set_game_id_': {
					'msg': "Введите PUBG ID матча [{game}], текущий PUBG ID: {pubg_id}",
					'input': {
						'msg_valid': "Новый PUBG ID для матча [{game}]: {new_id}",
						'msg_error': "Матч не найден",
						'msg_success': "PUBG ID установлен",
					}
				},
				'set_winners_': {
					'msg': (
						"Введите победителей в матче [{game}] - PUBG ID: {pubg_id}\n"
						"{winners}"
					),
					'input': {
						'msg_error': "Матч не найден",
						'msg_success': "Призы скоро будут распределены"
					},
					'next': {
						'place_': {
							'btn_template': "{place}: {username}",
							'msg': "Введите PUBG ник игрока, занявшего {} место",
							'input': {
								'msg_error': "Матч не найден",
								'msg_valid': "Игрок выбран"
							}
						},
					}
				},
			}
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
				'del_admin': {
					'btn': "Удалить администратора",
					'msg': "Администраторы:\n{}\nВыберите, кого удалить",
					'next': {}
				}
			}
		},
		'mailing': {
			'btn': "Отправить сообщения пользователям",
			'msg': "Здесь будет рассылка",
		},
	}
}
menu['next']['admin'].update(admin)
admin_added = "Администратор добавлен!"
admin_removed = "Администартор удалён!"
admin_update_failed = "Не получилось"
pubg_id_is_needed = "Матч [{}] начнётся через 20 минут! Введите PUBG ID матча."
goto_admin = "Перейти в админку"
set_game_winners = "Ввести результаты"
set_pubg_id = "Установить PUBG ID"

# misc
error = "Ошибка. Попробуйте заново"
back = "Назад"
main = "В главное меню"
confirm = "Подтвердить"
reset = "Сбросить выбор"
victory = (
	"*Поздравляем!*\n"
	"Матч [{}] завершён, вы заняли {} место, ваш баланс увеличен на {}."
)