#!/usr/bin/python

class Event(dict):
    def __init__(self, id, name, location, start_timestamp, end_timestamp):
        dict.__init__(self, id=id, name=name, location=location,
                start_timestamp=start_timestamp, end_timestamp=end_timestamp)
        self.name = name
        self.location = location
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        id = id
    def __str__(self):
            return str(self.__class__) + ": " + str(self.__dict__)


class User(dict):
    def __init__(self, email):
        dict.__init__(self, email=email)
        self.email = email
