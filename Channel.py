from Distribution import negative_exponential_distribution
from Event import DepartureEvent

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

    def transmit_df(self, df):
        pass

    def createDepartureEvent(self, event_time, df, type = "external DF"):
        def success():
            """
            If sucess, then schedule the arrival event in the receiver
            arrival_time = event_time
            :return:
            """
            arrival_time = event_time
            print("))))))", type)
            df.receiver.createArrivalDataFrameEvent(arrival_time, df.receiver, type, df)



        def failure():
            """
            no failure
            :return:
            """
            pass


        event_time = event_time + df.size / self.GEL.channel.rate
        departure = DepartureEvent(event_time, df, success, failure)
        self.GEL.addEvent(departure)

