"""Webhook returning list of games for website"""

import cherrypy as app
import psycopg2 as postgres

##############################

TEXTS = {
	'survival_easy': "Выживание (лёгкий)",
	'survival_medium': "Выживание (средний)",
	'survival_hard': "Выживание (тяжёлый)",
	'kills': "Убийства",
	"mixed": "Смешанный",
	'1st': "От первого лица",
	'3rd': "От третьего лица",
	'solo': "SOLO",
	'dual': "DUAL",
	'squad': "SQUAD",
	'payload': "Payload",
	'zombie': "Zombie",
}
DEFAULT = "Ещё не выбрано!"
GET_GAMES_QUERY =\
	"""
	SELECT TO_CHAR(time, 'HH24:MI'), bet, view, type, mode
	FROM MATCHES WHERE finished = false
	ORDER BY time
	"""

##############################


@app.expose
class GetGames():
	"""Returning list of not yet finished games at /games"""

	@app.tools.json_out()
	@app.tools.accept(media='application/json')
	def GET(self):
		try:
			with postgres.connect(app.config['database'], sslmode='require') as conn:
				with conn.cursor() as cursor:
					cursor.execute(GET_GAMES_QUERY)
					raw_games = cursor.fetchall()
		except postgres.Error as err:
			app.log.error(err.args[0], context=f"DB Error - {type(err).__name__}:\n")
			raise app.HTTPError(500)
		return [
			[TEXTS.get(data, data) if data else DEFAULT for data in game]
				for game in raw_games
		]


app.tree.mount(
	GetGames(), '/games',
	config={
		'/': {
			'request.dispatch': app.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [
				('Access-Control-Allow-Origin', '*'),
			],
		}
	}
)
