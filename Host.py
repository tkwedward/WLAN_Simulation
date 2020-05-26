from Buffer import Buffer
from DataFrame import DataFrame
from Event import ArrivalDataFrameEvent, DepartureEvent, SenseChannelEvent, DiscardEvent, PushToChannelEvent, AckExpectedEvent
from Distribution import negative_exponential_distribution
class Host(object):
    def __init__(self, number, gel):
        self.name = f"Host {number}"
        self.status = "idle"
        self.buffer = Buffer()
        self.channel = gel.channel
        self.GEL = gel
        self.arrivalRate = 0.8
        self.senseTime = 0.01            # 0.01 ms
        self.DIFS = 0.1                  # 0.10 ms
        self.SIFS = 0.05                 # 0.05 ms

    def random_backoff(self, dataframe)-> float:
        if n > 10:
            n = 10
        wait_time = random.randint(0, 2 ** n - 1) * 512 / CHANNEL_RATE * 1000
        return wait_time

    def addToBuffer(self, dataframe):
        self.buffer.append(dataframe)

    def createArrivalDataFrameEvent(self, event_time, receiver, name, df = None):
        """
        create one of the following arrival event and put it to the GEL event list
        external DF: df from external host to this host
            success => schedule receive event

        internal DF: df created in this host
            success => schedule receive event
            failure => put into the buffer

        ACK DF: ACK from external host
        """

        sender = self

        success = None
        failure = None

        if name == "internal DF":
            new_event_time = event_time + negative_exponential_distribution(self.arrivalRate)
            df = DataFrame("data", new_event_time, sender, receiver=receiver)
            def success():
                self.createSenseChannelEvent(new_event_time, df, "df, stage 0")

            def failure():
                pass

            arrival = ArrivalDataFrameEvent(name, new_event_time, sender, receiver, df, success, failure)

        elif name == "external DF":
            ack_time = event_time
            ack_sender = self
            ack_receiver = df.sender
            ack = DataFrame("ack", ack_time, ack_sender, ack_receiver)
            ack.size = 64
            def success():
                """
                To return an ACK to the sender
                ack_time = event_time
                :return:
                """

                self.createSenseChannelEvent(ack_time, ack, "ack, stage 0")
            def failure():
                """
                No failure
                :return:
                """
                pass

            arrival = ArrivalDataFrameEvent(name, ack_time, sender, receiver, df, success, failure)


        self.GEL.addEvent(arrival)

    def receiveDataframeEvent(self, event_time, df, type):
        if name == "internal DF":
            def success():
                self.createSenseChannelEvent(new_event_time, df, "df, stage 0")

            def failure():
                pass




    def createSenseChannelEvent(self, event_time, df, type, counter = None):
        """
        three types of sense event
            1) df, stage 0
            2) df, stage 1
            3) ack, stage 0
            4) ack, stage 1
            5) Countdown
        :param event_time:
        :param df:
        :param type:
        :param counter:
        :return:
        """
        success = None
        failure = None

        if type == "df, stage 0":
            """
            new_event_time = previous event time + 0.01 
            sucess: if sense idle, wait DIFS and then sense again
s
            2) sense of D
            fail: RBA
            """

            def success():
                sense_event_time = event_time + self.senseTime
                self.createSenseChannelEvent(sense_event_time, df, "df, stage 1")

            def failure():
                sense_event_time = event_time + self.senseTime
                self.createSenseChannelEvent(sense_event_time, df, "RBA")

        elif type == "df, stage 1":
            """
            new_event_time_1 = event_time + 0   
            success: send the data to the channel immediately
            
            new_event_time_2
            failure: RBA
            """

            def success():
                sense_event_time = event_time + self.DIFS
                self.createPushToChannelEvent(sense_event_time, df)

            def failure():
                sense_event_time = event_time + self.DIFS
                _counter = self.random_backoff(df)
                self.createSenseChannelEvent(sense_event_time, df, "Countdown", _counter)

        elif type == "ack, stage 0":
            """
            sense_time = event_time + 0.01
            
            """
            def success():

                sense_event_time = event_time + self.SIFS
                self.createSenseChannelEvent(sense_event_time, df, "ack, stage 1")

            def failure():
                pass

        elif type == "ack, stage 1":
            """
            if success, wait SIFS and then sense again, if it is still idle, then send the ACK immediately
            
            """
            print("ack, stage 1")
            def success():
                sense_event_time = event_time
                self.createPushToChannelEvent(sense_event_time, df)

        elif type == "Countdown":
            pass

        sense_event_time = event_time + self.senseTime
        senseChannelEvent = SenseChannelEvent(sense_event_time, type, df, success, failure)
        self.GEL.addEvent(senseChannelEvent)

    def createPushToChannelEvent(self, event_time, df):
        """
        pushEventTime = event_time + 0

        """

        def success():
            """
            If success, expect an ACK packet return
            new_event_time = event_time + transmission_time_df + transmission_time_ACK
            :return:
            """
            departure_time = event_time + df.size/self.channel.rate
            self.channel.createDepartureEvent(departure_time, df)

            expected_ACK_time = event_time + (df.size + 64) / self.channel.rate + self.senseTime * 2 + 1e-9
            self.createExpectAckEvent(expected_ACK_time, df)

        def failure():
            pass

        push_event_time = event_time + 0
        pushEvent = PushToChannelEvent(push_event_time, "push dataframe to channel Event", df, success, failure)
        self.GEL.addEvent(pushEvent)



    def createExpectAckEvent(self, event_time, df):
        """
        new_event_time = event_time + total_transmission_time (df and ACK) + SIFS + senseTime
        :param event_time:
        :param df:
        :return:
        """
        new_event_time = event_time + (df.size + 64) / self.channel.rate + self.SIFS*10 + 0.0001
        def success():
            pass


        def failure():
            pass

        _ackExpectEvent = AckExpectedEvent(new_event_time, df, success, failure)
        self.GEL.addEvent(_ackExpectEvent)


    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self.name)

