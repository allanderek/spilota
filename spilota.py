import requests
import bs4

class Spilota(object):
    def get(self, url):
        self.response = requests.get(url)
        self.soup = bs4.BeautifulSoup(self.response.text, 'html.parser')

    def get_element(self, css_selector):
        return getattr(self.soup, css_selector)

    def exists(self, css_selector):
        return bool(self.get_element(css_selector))

    def click(self, css_selector):
        element = self.get_element(css_selector)
        url = element['href']
        self.get(url)

# Testing.

import threading
import time

import pytest
import flask
from abc import ABCMeta, abstractproperty


class Application(object):
    @staticmethod
    def shutdown():
        """Shutdown the Werkzeug dev server, if we're using it.
        From http://flask.pocoo.org/snippets/67/"""
        func = flask.request.environ.get('werkzeug.server.shutdown')
        if func is None:  # pragma: no cover
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        return 'Server shutting down...'

    application = None # Poor man's abstract base class property

    @pytest.fixture(autouse=True)
    def server_thread(self, request):
        application = self.__class__.application
        application.add_url_rule('/shutdown', 'shutdown',
                                 self.shutdown, methods=['GET'])
        server_thread = threading.Thread(target=application.run)
        server_thread.start()

        pause = 0.1 # I'll pause 0.1 seconds between each poll/try
        num_tries = 50 # So I'll wait for around 5 seconds.
        for _ in range(num_tries):
            try:
                requests.get("http://localhost:5000/")
                break
            except:  # pragma: no cover
                time.sleep(pause)
        else:  # pragma: no cover
            print("Server does not seem to have been started!")
            pytest.fail('Could not start server thread.')

        def fin():
            requests.get("http://localhost:5000/shutdown")
            server_thread.join(timeout=3)
        request.addfinalizer(fin)
        return server_thread

@pytest.fixture(scope="module")
def driver():
    driver = Spilota()
    return driver

class TestHelloWorld(Application):
    application = flask.Flask('TestHelloWorld')

    @staticmethod
    @application.route("/")
    def hello():
        return "<h1>Hello World!</h1>"

    def test_application(self, driver):
        driver.get('http://localhost:5000')
        assert driver.exists('h1')
        assert not driver.exists('h2')

class TestClick(Application):
    application = flask.Flask('TestClick')

    @staticmethod
    @application.route("/")
    def hello():
        return """<h1>Hello World!</h1>
                  <a href="http://localhost:5000/goodbye">say goodbye</a>"""

    @staticmethod
    @application.route("/goodbye")
    def goodbye():
        return "<h2>Goodbye World!</h2>"

    def test_application(self, driver):
        # So this is essentially the actual test.
        driver.get('http://localhost:5000')
        assert driver.exists('h1')
        assert not driver.exists('h2')
        driver.click('a')
        assert driver.exists('h2')
        assert not driver.exists('h1')
