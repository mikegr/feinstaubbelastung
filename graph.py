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
        self.writeCount()
        self.write(datetime.datetime(2011, 1, 1), datetime.datetime(2011, 3, 31))
        self.write(datetime.datetime(2011, 4, 1), datetime.datetime(2011, 6, 30))
        self.write(datetime.datetime(2011, 7, 1), datetime.datetime(2011, 9, 30))
        self.write(datetime.datetime(2011, 10, 1), datetime.datetime(2011, 12, 31))
        self.response.out.write('</body></html>')
    
    def writeCount(self):
        dates  = db.GqlQuery("SELECT * FROM Data WHERE value > 50")
        title = "Taborstraße - Überschreitungen der Feinstaubbelastung seit Jahresbeginn:  " + str(dates.count())
        self.response.out.write('<h3>' + title + '</h3>');

    def write(self, fromDate, toDate):
        logging.info("WRITE")
        dates  = db.GqlQuery("SELECT * FROM Data WHERE date >=  :1 AND date <= :2 ORDER BY date ASC", fromDate, toDate)
        counter = 0
        below = ""
        above = ""
        width = "1000"
        last_date = fromDate
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

        date_fmt = "%d.%m.%Y"

        labels = "&chxt=x&chxr=0," + all + "&chxp=0," + all + "&chxl=0:|"+ fromDate.strftime(date_fmt) +"|" +  last_date.strftime(date_fmt)   + "&chm=N,000000,-1,,10&chdlp=t"
        """self.response.out.write('Werte:')
            for data in dates:
                self.response.out.write(cgi.escape(str(data.date)) + ":" + cgi.escape(str(data.value)))
        self.response.out.write('Werte-ENDE:')"""
        chartUrl = "http://chart.apis.google.com/chart?chdl=Nicht+überschritten|Überschritten&cht=bvs&chs="+ width + "x220&chco=FFBAB1,FF0000&chbh=a,1&chds=0,130"
        link = chartUrl + labels + "&chd=t:" + below[:-1] + "|" + above[:-1]
        self.response.out.write('<iframe src="' + link + '" width="1050" height="250"></iframe>')
        

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
        urlPart1 = "https://www.wien.gv.at/ma22-lgb/tb/"
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
                logging.info("URL: " + url)
                url_handle = urllib2.urlopen(url);
                for line in url_handle:
                    if (line.startswith("Taborstra&szlig;e")):
                        data = Data()
                        logging.debug("Line: " + line)                        
                        data.line = line
                        data.date = single_date
                        try:
                            data.value = int(line.split("|")[4].replace("*", "").strip())
                        except ValueError:
                            data.value = int("0")    
                        data.put();
                        out.write("Storing: " + str(data.date) + ":" +  str(data.value) + "<br/>")    
 

    def format_date(self, single_date):
        formatString = "%Y%m%d"
        return "tb" + single_date.strftime(formatString)  + ".htm"
        
    def daterange(self, start_date, end_date):
        for n in range((end_date - start_date).days):
            yield start_date + timedelta(n)


class LastValue(webapp.RequestHandler):
    def get(self):
        today = datetime.datetime.now();
        q = db.GqlQuery("SELECT * FROM Data ORDER BY date DESC LIMIT 1")
        green = '00FF00'
        red = 'FF0000'
        result = q.get()
        if (result.value > 50):
            color = red
        else:
            color = green

        head = '<head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /></head>'
        body1 = '<body><table style="border-style:solid;border-width:1px;position:relative;overflow: hidden;font-family:Helvetica, sans-serif;font-size:small;width:250px;"><tr style="border-style: none;"><td style="float:left;padding:10px;">Feinstaubbelastung Taborstraße ' 
        body2 = '</td><td style="background-color:#'
        body3 = ';width:100px;text-align:left;vertical-align:center;padding:20px;">'
        body4 = ' µg/m³</td></tr></table></body>'

        site = head + body1 + result.date.strftime("%d.%m.%Y") + body2 + color + body3 + str(result.value) + body4
        self.response.out.write(site)

class LastValues(webapp.RequestHandler):
    def get(self):
        count = int(self.request.get("count", "1"))
        today = datetime.datetime.now();
        q = db.GqlQuery("SELECT * FROM Data ORDER BY date DESC LIMIT " + str(count))
        green = '00FF00'
        red = 'FF0000'
        results = q.fetch(count)
        head = '<head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /></head>'

        body1 = '<body><table style="border-style:solid;border-width:1px;position:relative;overflow: hidden;font-family:Helvetica, sans-serif;font-size:small;"><tr style="border-style: none;"><td colspan="' + str(count)  + '" style="text-align:center;padding:5px;background-color:#EEEEEE">Feinstaubbelastung Taborstraße </td><tr>'
        body2 = '</tr><tr>'
        body3 = '</tr></table></body>'
        rows1 = rows2 = ""
        for  result in results:
            if (result.value > 50):
                color = red
            else:
                color = green
            rows1 = '<td style="text-align:center;vertical-align:center;">' + result.date.strftime("%d.%m.%Y") + '</td>' + rows1
            rows2 = '<td style="background-color:#' + color + ';width:75px;text-align:center;vertical-align:center;padding:5px;">' + str(result.value) + ' µg/m³</td>' + rows2

        site = head + body1 + rows1 + body2 + rows2 + body3
        self.response.out.write(site)



application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ("/parse", Parser),                                          
                                      ('/last1', LastValue),
                                      ('/last', LastValues)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
