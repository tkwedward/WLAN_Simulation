from Distribution import negative_exponential_distribution
from Event import DepartureEvent, ScheduleDataFrameEvent
from DataFrame import DataFrame

class Channel(object):
    def __init__(self, rate, gel):
        self.GEL = gel
        self.status = "idle"
        self.rate = rate # 11Mbps
        self.status_array = [("idle", 0)]

    def change_status(self, event_time):
        self.status = "busy" if self.status=="idle" else "idle"
        self.status_array.append((self.status, event_time))

    def get_busy_time(self):
        busy_time = 0
        for i in range(int(len(self.status_array[1:])/2)):
            busy_time += self.status_array[2*i+2][1] - self.status_array[2*i+1][1]
        return busy_time

    def createDepartureEvent(self, event_time: float, df: DataFrame, type:str = "external DF")->None:
        def success():
            """
            If sucess, then schedule the arrival event in the receiver
            arrival_time = event_time
            """

            arrival_time = event_time
            arrivalEvent = ScheduleDataFrameEvent(type, arrival_time, df.sender, df.receiver, self.GEL, df.origin, df)
            self.GEL.addEvent(arrivalEvent)

        departure = DepartureEvent(event_time, df, success, df.origin)
        self.GEL.addEvent(departure)

