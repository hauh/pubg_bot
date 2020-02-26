from logging import getLogger

import mysql.connector

import config
import queries

##############################

logger = getLogger('db')


def withConnection(db_request):
	def executeWithConnection(*args):
		try:
			connection = mysql.connector.connect(**config.db_kwargs)
			cursor = connection.cursor()
		except Exception as err:
			logger.critical(
				"DB connection failed with:\n{} {}"
					.format(type(err).__name__, err.args)
			)
		else:
			try:
				result = db_request(*args, cursor=cursor)
			except Exception as err:
				logger.error(
					"DB query failed with:\n{} {}"
						.format(type(err).__name__, err.args)
				)
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
