from DataFrame import DataFrame
DIFS = 0.1
SIFS = 0.05
SENSETIME = 0.01

class Event(object):
    def __init__(self, event_time):
        self.event_time = event_time
        self.previousEvent = None
        self.nextEvent = None

    def takeEffect(self, gel):
        if gel.channel.status == "idle":
            self.success()
        else:
            self.failure()

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.name}"


class ArrivalDataFrameEvent(Event):
    def __init__(self, name, event_time, sender, receiver, df, success, failure):
        super().__init__(event_time)
        self.name = name
        self.sender = sender
        self.receiver = receiver
        self.dataframe = df
        self.success = success
        self.failure = failure


    def takeEffect(self, gel):
        event_time = self.event_time
        sender = self.sender

        if sender.status == "idle":
            self.success()

        else:
            self.failure()


    def __str__(self):
        return f"{self.name}  {self.source}, {self.sender}, {self.receiver} "



class SenseChannelEvent(Event):
    def __init__(self, event_time, type, df, success, failure):
        super().__init__(event_time)
        self.type = type
        self.name = "sense channel, "+ type
        self.dataframe = df
        self.success = success
        self.failure = failure

class DiscardEvent(Event):
    def __init__(self, event_time, name):
        super().__init__(event_time)
        self.name = name

class PushToChannelEvent(Event):
    """
    The df is pushed to channel. Check if the channel is idle or busy
    If idle, then schedule arrival event of the df
    If busy, then discard the event
    """
    def __init__(self, event_time, name, df, success, failure):
        super().__init__(event_time)
        self.name = name
        self.dataframe = df
        self.success = success
        self.failure = failure

    def takeEffect(self, gel):
        if gel.channel.status == "idle":
            gel.channel.status = "busy"
            self.success()
        else:
            # pass to discard the item
            self.failure()
            pass

class DepartureEvent(Event):
    def __init__(self, event_time, df, success, failure):
        super().__init__(event_time)
        self.name = "Departure Event, " + df.type
        self.dataframe = df
        self.success = success
        self.failure = failure


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

    def __init__(self, event_time, df, success, failure):
        super().__init__(event_time)
        self.name = "Expect ACK"
        self.df = df
        self.success = success
        self.failure = failure


class CollisionEvent(Event):
    def __init__(self, event_time, packet=None):
        super().__init__(event_time, packet)
        self.name = "Collision"

class successTransferEvent(Event):
    def __init__(self, event_time, df, success, failure):
        super().__init__(event_time)
        self.name = "success transfer"
        self.dataframe = df
        self.success = success
        self.failure = failure

    def takeEffect(self, gel):
        self.success()

