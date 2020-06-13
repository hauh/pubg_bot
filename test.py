'''Testing module with server to catch requests'''

import logging
from threading import Thread
from queue import Queue, Empty
from http.server import HTTPServer, BaseHTTPRequestHandler

##############################

SERVER_ADDRESS = ('127.0.0.1', 7777)
REQUESTS_QUEUE = Queue()

logging.basicConfig(format="", level=logging.INFO)
logger = logging.getLogger('debug')

##############################


class BotRequestHandler(BaseHTTPRequestHandler):
	'''Catches POST requests and puts them to Queue for testing thread'''

	def log_message(self, *_):
		pass

	def do_POST(self):
		content_length = int(self.headers['Content-Length'])
		post_data = self.rfile.read(content_length).decode('unicode_escape')
		REQUESTS_QUEUE.put(post_data)
		self.send_response(200)
		self.end_headers()


def do_test(data):
	pass


def test():

	server = HTTPServer(SERVER_ADDRESS, BotRequestHandler)
	Thread(target=server.serve_forever).start()

	try:
		while True:
			data = REQUESTS_QUEUE.get(timeout=10)
			logger.info("Got data: %s", data)
			do_test(data)

	except Empty:
		pass

	server.shutdown()
	logger.info("Tests done")


if __name__ == '__main__':
	test()
