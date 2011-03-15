# coding=utf-8
import cgi
import logging
import datetime
import urllib2

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext import blobstore
from datetime import timedelta

class Data(db.Model):
    value = db.IntegerProperty()
    date = db.DateTimeProperty()
    line = db.TextProperty()

class MainPage(webapp.RequestHandler):
    def get(self):
		self.response.out.write('<html><body>')
		dates  = db.GqlQuery("SELECT * FROM Data ORDER BY date ASC")
		counter = 0
		below = ""
		above = ""
		width = "1000"
		for data in dates:
			last_date = data.date
			if (data.value > 50):	
				counter = counter + 1
				below += ("0,")
				above += (str(data.value) + ",")
			else:
				below +=  (str(data.value) + ",")
				above += ("0,")
		all = str(dates.count());
		title = "Taborstraße - Überschreitungen der Feinstaubbelastung seit Jahresbeginn:  " + str(counter)
		last_date_str = last_date.strftime("%d.%m.%Y")
		labels = "&chxt=x&chxr=0," + all + "&chxp=0," + all + "&chxl=0:|1.1|" +  last_date_str  + "&chm=N,000000,-1,,10&chdlp=t"
		"""self.response.out.write('Werte:')
        	for data in dates:
        	    self.response.out.write(cgi.escape(str(data.date)) + ":" + cgi.escape(str(data.value)))
		self.response.out.write('Werte-ENDE:')"""
		chartUrl = "http://chart.apis.google.com/chart?chtt="  + title + "&chdl=Nicht+überschritten|Überschritten&cht=bvs&chs="+ width + "x220&chco=FFBAB1,FF0000&chbh=a,1&chds=0,130"
		link = chartUrl + labels + "&chd=t:" + below[:-1] + "|" + above[:-1]
		self.response.out.write('<iframe src="' + link + '" width="1000" height="250"/>')
		


class Guestbook(webapp.RequestHandler):
    def post(self):
	logging.debug("START")
        data = Data()
	data.date  = datetime.datetime.strptime(self.request.get('datum'), "%d.%m.%Y")
	data.value = int(self.request.get('wert'))
        data.put()
        self.redirect('/')

class Parser(webapp.RequestHandler):
	def get(self):
		urlPart1 = "http://www.wien.gv.at/ma22-lgb/tb/"
		out = self.response.out
		first = datetime.datetime(2011, 1, 1)
		today = datetime.datetime.now();
		delta = timedelta(days=1)
		for single_date in self.daterange(first, today):

			q = db.GqlQuery("SELECT * FROM Data WHERE date = :1", single_date)
			result = q.get();
			if (result != None):
				out.write("in DB: " + str(result.date) +  ":" + str(result.value) + "</br>") 
			else:
				filename = self.format_date(single_date)		
				url = urlPart1 + filename;
				url_handle = urllib2.urlopen(url);
				for line in url_handle:
					if (line.startswith("Taborstra&szlig;e")):
						data = Data()
						data.line = line
						data.date = single_date
						data.value = int(line.split("|")[4].replace("*", "").strip())
						data.put();
						out.write("Storing: " + str(data.date) + ":" +  str(data.value) + "<br/>")	
 

	def format_date(self, single_date):
		formatString = "%Y%m%d"
		return "tb" + single_date.strftime(formatString)  + ".htm"
		
	def daterange(self, start_date, end_date):
	    for n in range((end_date - start_date).days):
	        yield start_date + timedelta(n)


application = webapp.WSGIApplication(
                                     [('/', MainPage),
									  ("/parse", Parser),									  	
                                      ('/sign', Guestbook)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
