tables = (
	"""
		CREATE TABLE IF NOT EXISTS matches (
			id		INT PRIMARY KEY AUTO_INCREMENT,
			mode	ENUM('solo', 'dual', 'squad'),
			view	ENUM('1st', '3rd'),
			bet		ENUM('30', '60', '90'),
			closed	BOOL DEFAULT false
		)
	""",
	"""
		CREATE TABLE IF NOT EXISTS users (
			id		INT PRIMARY KEY,
			pubg_id	INT,
			balance	INT	DEFAULT 0
		)
	""",
	"""
		CREATE TABLE IF NOT EXISTS balance_history (
			id		INT PRIMARY KEY AUTO_INCREMENT,
			amount	INT NOT NULL,
			user_id	INT,
			date	DATETIME,
			FOREIGN KEY (user_id) REFERENCES users (id)
		)
	""",
)

get_matches =\
	"""
		SELECT * FROM matches WHERE
			closed = false
			AND (mode = %(mode)s OR %(mode)s is NULL)
			AND (view = %(view)s OR %(view)s is NULL)
			AND (bet = %(bet)s OR %(bet)s is NULL)
	"""

get_user =\
	"""
		SELECT * FROM users WHERE id = %s
	"""

save_user =\
	"""
		INSERT INTO users (id) VALUES (%s)
	"""

update_balance = (
	"""
		UPDATE users SET balance = balance + %s WHERE id = %s
	""",
	"""
		INSERT INTO balance_history (amount, user_id, date)
			VALUES (%s, %s, NOW())
	""",
)

update_pubg_id =\
	"""
		UPDATE users SET pubg_id = %s WHERE id = %s
	"""

get_balance_history =\
	"""
		SELECT * FROM balance_history WHERE
			(user_id = %(user_id)s OR %(user_id)s is NULL)
	"""
