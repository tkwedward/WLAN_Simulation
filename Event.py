from DataFrame import DataFrame
DIFS = 0.1
SIFS = 0.05
SENSETIME = 0.01

class Event(object):
    def __init__(self, event_time):
        self.event_time = event_time
        self.previousEvent = None
        self.nextEvent = None

    def takeEffect(self):
        pass

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.name}"


class ArrivalDataFrameEvent(Event):
    def __init__(self, name, event_time, source, sender, receiver, df):
        super().__init__(event_time)
        self.name = name
        self.source = source
        self.sender = sender
        self.receiver = receiver
        self.dataframe = df

    def takeEffect(self, gel):


        event_time = self.event_time
        sender = self.sender
        receiver = self.receiver
        df = self.dataframe

        if self.source == self.sender:
            # check is this packet is for sending to other host or some one send it to this host
            if sender.status == "idle":
                self.success()
            else:
                self.failure()
        else:
            """
            to return an ACK packet
            """
            self.name = "Arrival_DataFrame, " + self.dataframe.type
            received_df = self.dataframe
            ACK_sender = received_df.receiver
            ACK_receiver = received_df.sender

            ACK_sender.createReturnACKEvent(event_time, ACK_receiver)




    def __str__(self):
        return f"{self.name}  {self.source}, {self.sender}, {self.receiver} "

class ArrivalAckEvent(Event):
    def __init__(self, event_time, source, sender, receiver, df=None):
        super().__init__(event_time)
        self.name = "Arrival_ACK"
        self.source = source
        self.sender = sender
        self.receiver = receiver
        self.dataframe = df



class SenseChannelEvent(Event):
    def __init__(self, event_time, _type, df):
        super().__init__(event_time)
        self.type = _type
        self.name = "sense channel, "+ _type
        self.dataframe = df

    def takeEffect(self, gel):
        if self.type == "df, stage 0":
            """
            currentTime = previous event time + 0.01 (already pass the sense time) 
            sucess: if sense idle, wait DIFS and then sense again
            fail: RBA
            """

            self.successEventList = [SenseChannelEvent(self.event_time + DIFS + SENSETIME, "df, stage 1", self.dataframe)] # if success, wait for DIFS
            self.failEvent = SenseChannelEvent(self.event_time, "df, countdown", self.dataframe)

        elif self.type == "df, stage 1":
            """
            success: push to channel, the 0.001 ms added in the AckExpectedEvent is to ensure that the channel gets ACK before this event happens.
            """
            df_transmission_time = self.dataframe.size / gel.channel.rate
            ACK_transmission_time = 64 / gel.channel.rate
            self.successEventList = [PushToChannelEvent(self.event_time, "push to Channel", self.dataframe), AckExpectedEvent(self.event_time + df_transmission_time + SIFS + SENSETIME + ACK_transmission_time + 1e-9, self.dataframe)]
            self.failEvent = SenseChannelEvent(self.event_time + SENSETIME, "df, countdown", self.dataframe)


        elif self.type == "ACK, stage 0":
            transmission_time = self.dataframe.size / gel.channel.rate
            self.successEventList = [SenseChannelEvent(self.event_time + SIFS, "ACK, stage 1", self.dataframe)] # if success, wait for SIFS
            self.failEvent = IgnoreEvent(self.event_time, "Ignore ACK")

        elif self.type == "ACK, stage 1":
            self.successEventList = [
                PushToChannelEvent(self.event_time, "PushToChannelEvent", self.dataframe)]
            self.failEvent = IgnoreEvent(self.event_time, "Ignore ACK")
        elif self.type == "df, countdown":
            pass

        if gel.channel.status == "idle":
            for event in self.successEventList:
                gel.addEvent(event)
        else:
            gel.addEvent(self.failEvent)

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
    def __init__(self, event_time, type, df):
        super().__init__(event_time)
        self.name = "Push to Channel"
        self.dataframe = df

    def takeEffect(self, gel):
        event_time = self.event_time + self.dataframe.size / gel.channel.rate

        self.successEventList = [DepartureEvent(event_time, self.dataframe)]

        if gel.channel.status == "idle":
            gel.channel.status = "busy"
            for event in self.successEventList:
                gel.addEvent(event)
        else:
            # pass to discard the item
            pass

class DepartureEvent(Event):
    def __init__(self, event_time, df):
        super().__init__(event_time)
        self.name = "Departure Event, " + df.type
        self.dataframe = df

    def takeEffect(self, gel):
        gel.channel.status = "idle"
        source = self.dataframe.receiver
        sender = self.dataframe.sender
        receiver = self.dataframe.receiver
        gel.addEvent(ArrivalDataFrameEvent(self.event_time, source, sender, receiver, self.dataframe))



class AckExpectedEvent(Event):
    """
    After pushing the df to channel, an ACK is expected to come back
    If ACK is received, then
    """

    def __init__(self, event_time, df):
        super().__init__(event_time)
        self.name = "Expect ACK"

    def event_take_action(self):
        pass


class sendACKEvent(Event):
    def __init__(self, event_time, packet=None):
        super().__init__(event_time, packet)
        self.name = "ACK"

    def event_take_action(self):
        pass

class CollisionEvent(Event):
    def __init__(self, event_time, packet=None):
        super().__init__(event_time, packet)
        self.name = "Collision"

    def event_take_action(self):
        pass

