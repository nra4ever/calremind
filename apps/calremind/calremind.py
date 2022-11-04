import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, timedelta, time
from requests import get
import json

class CalHandler(hass.Hass):
    def initialize(self):
        #HA Server IP
        self.serverip = self.args["server_ip"]
        #HA Port
        port = "8123"
        if self.args["ha_port"]:
            port = self.args["ha_port"]
        self.serverport = port
        #Long lived access token from HA
        self.apikey = self.args["ha_token"]
        #entity ID of HA calendar
        self.calID = self.args["calendar_id"]
        #max number of upcoming events to handle
        maxe = 3
        if self.args["max_events"]:
            maxe = self.args["max_events"]
        self.maxEvents = maxe
        #how many hours before appointment should event be added to sensor
        haway = 48
        if self.args["hours_away"]:
            haway = self.args["hours_away"]
        self.hoursaway = haway
        #second field (1 in the default case) represents minute past the hour the script will run
        rt = time(00, 29, 0)
        #changing the "sensor.calremind" value below will allow you to change the name of the generated sensor
        sens = "sensor.calremind"
        if self.args["sensor_id"]:
            sens = self.args["sensor_id"]        
        self.calremind = self.get_entity(sens)
        #Changing this value to 1 will make sensor attribute indices begin at 1 instead of 
        ioff = 0
        if self.args["index_offset"]:
            ioff = self.args["index_offset"]
        self.indexOffset = ioff
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
                appTime = appointment["start"]["dateTime"][:-9]
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
                    "time{}".format(str(i + self.indexOffset)): appTime.split("T")[1],
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
