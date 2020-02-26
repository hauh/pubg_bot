tables = (
	"""
		CREATE TABLE IF NOT EXISTS matches (
			id		INT PRIMARY KEY AUTO_INCREMENT,
			mode	ENUM('solo', 'dual', 'squad'),
			view	ENUM('1st', '3rd'),
			bet		ENUM('30', '60', '90'),
			closed	BOOL DEFAULT(FALSE)
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
