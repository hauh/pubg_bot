tables = (
	"""
		SET timezone = 'Europe/Moscow'
	""",
	"""
		CREATE TYPE mode_t AS ENUM ('solo', 'dual', 'squad', 'payload', 'zombie')
	""",
	"""
		CREATE TYPE view_t AS ENUM ('1st', '3rd')
	""",
	"""
		CREATE TYPE bet_t AS ENUM ('30', '60', '90')
	""",
	"""
		CREATE TABLE IF NOT EXISTS matches (
			id			SERIAL PRIMARY KEY,
			mode		mode_t,
			view		view_t,
			bet			bet_t,
			closed		BOOL DEFAULT false
		)
	""",
	"""
		CREATE TABLE IF NOT EXISTS users (
			id			INT PRIMARY KEY,
			chat_id		INT NOT NULL,
			pubg_id		INT,
			username	VARCHAR(32),
			balance		INT	DEFAULT 0,
			admin		BOOL DEFAULT false
		)
	""",
	"""
		CREATE TABLE IF NOT EXISTS balance_history (
			id			SERIAL PRIMARY KEY,
			amount		INT NOT NULL,
			user_id		INT,
			date		TIMESTAMPTZ,
			FOREIGN 	KEY (user_id) REFERENCES users (id)
		)
	""",
)

get_matches =\
	"""
		SELECT * FROM matches WHERE
			closed = false
			AND (%(mode)s is NULL OR mode = %(mode)s)
			AND (%(view)s is NULL OR view = %(view)s)
			AND (%(bet)s is NULL OR bet = %(bet)s)
	"""

get_user =\
	"""
		SELECT * FROM users WHERE
			(%(id)s IS NULL OR id = %(id)s) AND
			(%(username)s IS NULL OR username = %(username)s)
	"""

get_user_by_username =\
	"""
		SELECT * FROM users WHERE username = %s
	"""

save_user =\
	"""
		INSERT INTO users (id, chat_id, username) VALUES (%s, %s, %s)
			ON CONFLICT (id) DO UPDATE SET
				chat_id = EXCLUDED.chat_id,
				username = EXCLUDED.username
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

get_admins =\
	"""
		SELECT * FROM users WHERE admin = true
	"""

update_admin =\
	"""
		UPDATE users SET admin = %s WHERE id = %s
	"""
