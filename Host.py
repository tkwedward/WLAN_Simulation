from Buffer import Buffer
from DataFrame import DataFrame
from Event import ArrivalDataFrameEvent, DepartureEvent, SenseChannelEvent, DiscardEvent
from Distribution import negative_exponential_distribution
class Host(object):
    def __init__(self, number, gel):
        self.name = f"Host {number}"
        self.status = "idle"
        self.buffer = Buffer()
        self.channel = gel.channel
        self.GEL = gel
        self.arrivalRate = 0.1

    def random_backoff(self, dataframe)-> float:
        if n > 10:
            n = 10
        wait_time = random.randint(0, 2 ** n - 1) * 512 / CHANNEL_RATE * 1000
        return wait_time

    def addToBuffer(self, dataframe):
        self.buffer.append(dataframe)

    def createArrivalDataFrameEvent(self, receiver):
        source = self
        sender = self
        event_time = self.GEL.current_time + negative_exponential_distribution(self.arrivalRate)

        df = DataFrame("data", event_time, sender, receiver)


        def success():
            sender.processing_df = df
            sender.createSenseChannelEvent(event_time + 0.01, "df, stage 0", df)

        def failure():
            self.addToBuffer(df)

        arrivalEvent = ArrivalDataFrameEvent("Arrival dataframe", event_time, source, sender, receiver, df)
        arrivalEvent.success = success
        arrivalEvent.failure = failure
        return arrivalEvent


    def createSenseChannelEvent(self, event_time, name, df):
        def success():
            pass

        def failure():
            pass

        senseEvent = SenseChannelEvent(event_time, name, df)
        senseEvent.success = success
        senseEvent.failure = failure

        self.GEL.addEvent(senseEvent)



    def createDepartureEvent(self, df):
        departureEvent = DepartureEvent()
        departureEvent.dataframe = df
        return departureEvent



    def createReturnACKEvent(self, event_time, receiver):
        df = DataFrame("ACK", event_time, self, receiver)
        arrivalAckEvent = ArrivalAckEvent(event_time, self, self, receiver, df)

        def success():
            self.processing_df = df
            nextEvent = SenseChannelEvent(event_time + 0.01, "ACK, stage 0", df)
            self.GEL.addEvent(nextEvent)

        def failure():
            pass

        arrivalAckEvent.success = success
        arrivalAckEvent.failure = failure

        return arrivalAckEvent

    def sendACK(self, target):
        pass

    def sense_channel(self) -> str:
        """
        To sense whether the channel is busy or not.
        """
        status = ""
        return status

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self.name)

