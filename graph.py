import cgi
import logging
import datetime

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

class Data(db.Model):
    value = db.IntegerProperty()
    date = db.DateTimeProperty()

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write('<html><body>')

        dates  = db.GqlQuery("SELECT * FROM Data ORDER BY date DESC LIMIT 10")
	self.response.out.write('Werte:')
        for data in dates:
            self.response.out.write(cgi.escape(str(data.date)) + ":" + cgi.escape(str(data.value)))

	self.response.out.write('Werte-ENDE:')
        # Write the submission form and the footer of the page
        self.response.out.write("""
              <form action="/sign" method="post">
		<div><textarea name="datum" rows="1" cols="20"></textarea></div>
                <div><textarea name="wert" rows="1" cols="20"></textarea></div>
                <div><input type="submit" value="Wert eintragen"></div>
              </form>
            </body>
          </html>""")

class Guestbook(webapp.RequestHandler):
    def post(self):
	logging.debug("START")
        data = Data()
	data.date  = datetime.datetime.strptime(self.request.get('datum'), "%d.%m.%Y")
	data.value = int(self.request.get('wert'))
        data.put()
        self.redirect('/')

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/sign', Guestbook)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
