from logging import getLogger
from os import getenv

import psycopg2
import psycopg2.extras

import queries as queries

##############################

logger = getLogger('db')
db_url = getenv('HEROKU_DB')


def withConnection(db_request):
	def executeWithConnection(*args, **kwargs):
		try:
			connection = psycopg2.connect(db_url, sslmode='require')
			cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
		except Exception as err:
			logger.critical(
				"DB connection failed with:\n{} {}"
					.format(type(err).__name__, err.args)
			)
			raise
		try:
			result = db_request(cursor, *args, **kwargs)
		except Exception as err:
			logger.error(
				"DB query failed with:\n{} {}"
					.format(type(err).__name__, err.args)
			)
			raise
		else:
			connection.commit()
			return result
		finally:
			cursor.close()
			connection.close()
	return executeWithConnection


@withConnection
def prepareDB(cursor):
	for create_table in queries.tables:
		cursor.execute(create_table)
	logger.info("Database ready!")


@withConnection
def getMatches(cursor, filters):
	cursor.execute(queries.get_matches, filters)
	return cursor.fetchall()


@withConnection
def getUser(cursor, user_id=None, username=None,
			pubg_username=None, pubg_id=None):
	cursor.execute(
		queries.get_user,
		{
			'id': user_id, 'username': username,
			'pubg_username': pubg_username, 'pubg_id': pubg_id
		}
	)
	return cursor.fetchone()


@withConnection
def saveUser(cursor, user_id, username):
	cursor.execute(queries.save_user, (user_id, username))
	logger.info("New user {} has been registered".format(user_id))


@withConnection
def updateBalance(cursor, user_id, amount):
	for query in queries.update_balance:
		cursor.execute(query, (amount, user_id,))
	cursor.execute(
		queries.get_user,
		{'id': user_id, 'username': None, 'pubg_username': None, 'pubg_id': None}
	)
	logger.info(
		"Balance of user {} has been changed for {}".format(user_id, amount))
	return cursor.fetchone()['balance']


@withConnection
def updatePubgID(cursor, user_id, pubg_id):
	cursor.execute(queries.update_pubg_id, (pubg_id, user_id,))
	logger.info("User {} has set their PUBG ID to {}".format(user_id, pubg_id))


@withConnection
def updatePubgUsername(cursor, user_id, pubg_username):
	cursor.execute(queries.update_pubg_username, (pubg_username, user_id,))
	logger.info(
		"User {} has set their PUBG username to {}".format(user_id, pubg_username))


@withConnection
def getBalanceHistory(cursor, user_id=None):
	cursor.execute(queries.get_balance_history, {'user_id': user_id})
	return cursor.fetchall()


@withConnection
def getAdmins(cursor):
	cursor.execute(queries.get_admins)
	return cursor.fetchall()


@withConnection
def updateAdmin(cursor, user_id, new_status):
	cursor.execute(queries.update_admin, (new_status, user_id))
	if cursor.rowcount == 0:
		return False
	if new_status:
		logger.info("User {} became admin".format(user_id))
	else:
		logger.info("User {} is no longer admin".format(user_id))
	return True
