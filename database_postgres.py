from logging import getLogger
from os import getenv

import psycopg2
import psycopg2.extras

import queries_postgress as queries

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
			result = db_request(*args, **kwargs, cursor=cursor)
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
def prepareDB(cursor=None):
	for table in queries.tables:
		cursor.execute(table)
	logger.info("Database ready!")


@withConnection
def saveMatches(cursor=None):
	for mode in ['solo', 'dual', 'squad']:
		for view in ['1st', '3rd']:
			for bet in ['30', '60', '90']:
				cursor.execute(
					"""
						INSERT INTO matches(mode, view, bet)
						VALUES (%s, %s, %s)
					""",
					(mode, view, bet)
				)
	logger.info("Matches updated")


@withConnection
def getMatches(filters, cursor=None):
	cursor.execute(queries.get_matches, filters)
	return cursor.fetchall()


@withConnection
def getUser(user_id=None, username=None, cursor=None):
	cursor.execute(queries.get_user, {'id': user_id, 'username': username})
	return cursor.fetchone()


@withConnection
def saveUser(user_id, chat_id, username, cursor=None):
	cursor.execute(queries.save_user, (user_id, chat_id, username))
	logger.info("New user {} has been registered".format(user_id))


@withConnection
def updateBalance(user_id, amount, cursor=None):
	for query in queries.update_balance:
		cursor.execute(query, (amount, user_id,))
	logger.info("Balance of {} has been changed for {}".format(user_id, amount))


@withConnection
def updatePubgID(user_id, pubg_id, cursor=None):
	cursor.execute(queries.update_pubg_id, (pubg_id, user_id,))
	logger.info("User {} has set their PUBG ID to {}".format(user_id, pubg_id))


@withConnection
def getBalanceHistory(user_id=None, cursor=None):
	cursor.execute(queries.get_balance_history, {'user_id': user_id})
	return cursor.fetchall()


@withConnection
def getAdmins(cursor=None):
	cursor.execute(queries.get_admins)
	return cursor.fetchall()


@withConnection
def updateAdmin(user_id, new_status, cursor=None):
	cursor.execute(queries.update_admin, (new_status, user_id))
	if cursor.rowcount == 0:
		return False
	if new_status:
		logger.info("User {} became added".format(user_id))
	else:
		logger.info("User {} is no longer admin".format(user_id))
	return True
