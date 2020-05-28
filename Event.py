from DataFrame import DataFrame
from Distribution import negative_exponential_distribution
from configuration_file import ARRIVE_RATE
DIFS = 0.1
SIFS = 0.05
SENSETIME = 0.01


class Event(object):
    def __init__(self, event_time):
        self.event_time = event_time
        self.previousEvent = None
        self.nextEvent = None

    def success(self):
        pass

    def failure(self):
        pass

    def takeEffect(self, gel):
        if gel.channel.status == "idle":
            self.success()
        else:
            self.failure()

    def __str__(self):
        return "trila"

    def __repr__(self):
        return "trial"

class ScheduleDataFrameEvent(Event):
    """
    just put the item into the GEL, no other function
    """
    def __init__(self, _type, event_time, sender, receiver, origin, gel, df=None):
        self.type = _type
        self.event_time = event_time
        self.sender = sender
        self.receiver = receiver
        self.origin = origin
        self.GEL = gel
        self.df = df

        if self.type == "internal DF":
            """
            The origin of an internal DF is the sender
            The origin of an external DF is the origin of the df
            The origin of an ack is the origin of the df
            """
            arrival_time = event_time + negative_exponential_distribution(ARRIVE_RATE)
            df = DataFrame("data", arrival_time, self.sender, self.receiver, self.sender.ackId, origin=self)
            self.GEL.packet_counter += 1
            self.sender.ackId += 1

            def success():
                self.sender.processArrivalDataFrame(arrival_time, self.receiver, "internal DF", df, df.origin)

            arrival_Event = ProcessDataFrameArrivalEvent(self.type, arrival_time, self.sender, self.receiver, df)
            arrival_Event.success = success
            self.GEL.addEvent(arrival_Event)

    def description(self):
        return f"Schedule Dataframe {self.type}, {self.event_time}"


class ProcessDataFrameArrivalEvent(Event):
    def __init__(self, _type, event_time, sender, receiver, df):
        super().__init__(event_time)
        self.type = _type
        self.sender = sender
        self.receiver = receiver
        self.dataframe = df
        self.origin = df.origin


    def takeEffect(self, gel):
        event_time = self.event_time
        sender = self.sender

        if sender.status == "idle":
            print("yes")
            self.success()

        else:
            self.failure()

    def description(self):
        return f"process {self.type}, {self.event_time}"

    def __str__(self):
        return f"{self._type}  {self.source}, {self.sender}, {self.receiver} "



class SenseChannelEvent(Event):
    def __init__(self, event_time, _type, df, success, failure, origin):
        super().__init__(event_time)
        self.type = _type
        self.dataframe = df
        self.success = success
        self.failure = failure
        self.origin = origin

    def description(self):
        return f"sense channel, {self.type}, {self.event_time}"

class PushToChannelEvent(Event):
    """
    The df is pushed to channel. Check if the channel is idle or busy
    If idle, then schedule arrival event of the df
    If busy, then discard the event
    """
    def __init__(self, event_time, _type, df, success, failure, origin):
        super().__init__(event_time)
        self.type = _type
        self.dataframe = df
        self.success = success
        self.failure = failure
        self.origin = origin

    def takeEffect(self, gel):
        if gel.channel.status == "idle":
            gel.channel.status = "busy"
            self.success()
        else:
            # pass to discard the item
            self.failure()

    def description(self):
        return f"PushToChannelEvent, {self.event_time}"

class DepartureEvent(Event):
    def __init__(self, event_time, df, success, failure, origin):
        super().__init__(event_time)
        print(df.type)
        self.type = df.type
        self.dataframe = df
        self.success = success
        self.failure = failure
        self.origin = origin

    def description(self):
        return f"Departure Event, {self.dataframe.type}, {self.event_time}"

    def takeEffect(self, gel):
        if gel.channel.status == "busy":
            gel.channel.status = "idle"
            self.success()
        else:
            # pass to discard the item
            self.failure()


class AckExpectedEvent(Event):
    """
    After pushing the df to channel, an ACK is expected to come back
    If ACK is received, then
    """

    def __init__(self, event_time, df, success, failure, origin):
        super().__init__(event_time)
        self.type = "Expect ACK"
        self.dataframe = df
        self.success = success
        self.failure = failure
        self.origin = origin

    def takeEffect(self, gel):
        sender = self.dataframe.sender
        if sender.notACKedDict[self.dataframe.id].ACKed == True:
            self.failure()
        else:
            self.success()

    def description(self):
        return f"Acknowledge, {self.dataframe.type}, {self.event_time}"

class SuccessTransferEvent(Event):
    def __init__(self, event_time, df, success, failure, origin):
        super().__init__(event_time)
        self.type = "success transfer"
        self.dataframe = df
        self.success = success
        self.failure = failure
        self.origin = origin

    def takeEffect(self, gel):
        self.success()




    def description(self):
        return f"df._type, {self.dataframe.type}, {self.event_time}"

