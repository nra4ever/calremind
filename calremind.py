import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, timedelta, time
from requests import get
import json

class CalHandler(hass.Hass):
    def initialize(self):
        ###############################################
        #               USER CONFIG BELOW             #
        ###############################################
        #HA Server IP
        self.serverip = "192.168.1.122"
        #HA Port
        self.serverport = "8123"
        #Long lived access token from HA
        self.apikey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0NDAyZjczN2UyMDM0ZDRiYmRiOWEzNTM1YzFjYjA2YiIsImlhdCI6MTY2NzI3NjkxNywiZXhwIjoxOTgyNjM2OTE3fQ.H6LoBa6vRiQ8cwwMTqUcAIaUl2DsIrtgYcjmtshjxuo"
        #entity ID of HA calendar
        self.calID = "calendar.work"
        #max number of upcoming events to handle
        self.maxEvents = 3
        #how many hours before appointment should event be added to sensor
        self.hoursaway = 48
        #second field (1 in the default case) represents minute past the hour the script will run
        rt = time(00, 29, 0)
        #changing the "sensor.calremind" value below will allow you to change the name of the generated sensor
        self.calremind = self.get_entity('sensor.calremind')
        #Changing this value to 1 will make sensor attribute indices begin at 1 instead of 0
        self.indexOffset = 0
        ###############################################
        #              USER CONFIG ENDS!!!            #
        ###############################################
        #callback hook
        self.run_hourly(self.calcheck, rt)
        #set headers for REST api
        self.headers = {
            "Authorization": "Bearer {}".format(self.apikey),
            "content-type": "application/json",
        }
        #initialise event array
        self.eventArr = []

    def calcheck(self, data, **kwargs):
        # Get and format now and later times
        now = datetime.now()
        later = now + timedelta(hours=self.hoursaway)
        micro = datetime.strftime(now, "%f")
        thetime = datetime.strftime(now, "T%H:%M:%S.{}Z".format(micro[:-3]))
        # Format REST api URL
        restcalurl = "http://{4}:{5}/api/calendars/{0}?start={1}{3}&end={2}{3}".format  \
            (self.calID, datetime.strftime(now, "%Y-%m-%d"), datetime.strftime(later, "%Y-%m-%d"), \
            thetime, self.serverip, self.serverport)
        # Get Response and parse
        parsed_summary = json.loads(get(restcalurl, headers=self.headers).text)
        self.eventArr = parsed_summary[:self.maxEvents]
        arrlen = len(self.eventArr)
        # If List is not empty, process events
        if arrlen > 0:
            for appointment in self.eventArr:
                #get current index
                i = self.eventArr.index(appointment)
                #format time and date for sensor
                appTime = appointment['start']['dateTime'][:-9]
                ato = datetime.strptime(appTime, "%Y-%m-%dT%H:%M")
                appDate_hr = datetime.strftime(ato, "%a %d %b")
                #if location is provided, load it into location variable
                location = ""
                if appointment["location"]:
                    location = appointment["location"]
                #Publish sensor
                self.log("Publishing " + appointment["summary"] + " event to sensor.")
                self.calremind.set_state(state=arrlen, attributes= { \
                    "event{}".format(str(i + self.indexOffset)): "on",
                    "name{}".format(str(i + self.indexOffset)): appointment["summary"],
                    "date{}".format(str(i + self.indexOffset)): appDate_hr,
                    "time{}".format(str(i + self.indexOffset)): appTime.split('T')[1],
                    "location{}".format(str(i + self.indexOffset)): location
                })
            #if list under maximum, set higher states to off
            if len(self.eventArr) < 3:
                self.calremind.set_state(state=arrlen, attributes= { \
                    "event{}".format(2 + self.indexOffset): "off"})
                if len(self.eventArr) < 2:
                    self.calremind.set_state(state=arrlen, attributes= { \
                        "event{}".format(1 + self.indexOffset): "off"})
        # If list is empty, set all states to off
        else:
            for i in range(0, self.maxEvents - 1):
                self.calremind.set_state(state="0", attributes={ \
                    "event{}".format(str(i + self.indexOffset)): "off"})
