import requests
import bs4

class Spilota(object):
    def get(self, url):
        self.response = requests.get(url)
        self.soup = bs4.BeautifulSoup(self.response.text, 'html.parser')

    def exists(self, css_selector):
        return bool(getattr(self.soup, css_selector))

# Testing.

import threading
import time

import pytest
import flask

application = flask.Flask(__name__)

@application.route("/")
def hello():
    return "<h1>Hello World!</h1>"

@application.route("/shutdown")
def shutdown():
    """Shutdown the Werkzeug dev server, if we're using it.
    From http://flask.pocoo.org/snippets/67/"""
    func = flask.request.environ.get('werkzeug.server.shutdown')
    if func is None:  # pragma: no cover
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


@pytest.fixture(scope="module")
def driver():
    driver = Spilota()
    return driver

@pytest.fixture(scope="module")
def server_thread(request):
    server_thread = threading.Thread(target=application.run)
    server_thread.start()

    pause = 0.1 # I'll pause 0.1 seconds between each poll/try
    num_tries = 50 # So I'll wait for around 5 seconds.
    for _ in range(num_tries):
        try:
            response = requests.get("http://localhost:5000/")
            break
        except:
            time.sleep(0.1)
    else:
        print("Server does not seem to have been started!")
        pytest.fail('Could not start server thread.')

    def fin():
        response = requests.get("http://localhost:5000/shutdown")
        server_thread.join(timeout=3)
    request.addfinalizer(fin)
    return server_thread

def test_application(server_thread, driver):
    # So this is essentially the actual test.
    driver.get('http://localhost:5000')
    assert driver.exists('h1')
    assert not driver.exists('h2')
