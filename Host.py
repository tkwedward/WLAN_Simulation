from Buffer import Buffer
from DataFrame import DataFrame
from Distribution import negative_exponential_distribution
from Event import ArrivalDataFrameEvent, SenseChannelEvent, PushToChannelEvent, AckExpectedEvent, successTransferEvent
import random


class Host(object):
    def __init__(self, number: int, gel: "Global Event List"):
        self.name = f"Host {number}"
        self.status = "idle"
        self.buffer = Buffer()
        self.channel = gel.channel
        self.GEL = gel
        self.arrivalRate = 0.8           # lambda
        self.senseTime = 0.01            # 0.01 ms
        self.DIFS = 0.1                  # 0.10 ms
        self.SIFS = 0.05                 # 0.05 ms
        self.notACKedDict = {}
        self.ackId = 0

    def random_backoff(self, n: int)-> float:
        """
        To generate random backoff counter value
        :param df: the dataframe which we can get the number of collision n from it
        :return: Random backoof counter value
        """
        if n > 10:
            n = 10
        wait_time = random.randint(0, 2 ** n - 1)
        return wait_time

    def addToBuffer(self, df: DataFrame):
        self.buffer.append(df)

    def createArrivalDataFrameEvent(self, event_time: float, receiver: "Host", name: str, df = None, origin = None) -> ArrivalDataFrameEvent:
        """
        create one of the following arrival event and put it to the GEL event list

        internal DF: df created in this host
            success => schedule sense event to see if the channel is idle to process the df
            failure => put into the buffer

        external DF: df from external host to this host
            success => schedule receive event and then return an ACK latter
            failure => no failure

        ACK DF: ACK from external host
            success => take the next df from the buffer and process it
            failure => no failure
        """

        sender = self

        success = None
        failure = None
        arrival = None

        if name == "internal DF":
            new_event_time = event_time + negative_exponential_distribution(self.arrivalRate)
            df = DataFrame("data", new_event_time, sender, receiver, self.ackId, origin=self)
            self.GEL.packet_counter += 1
            self.ackId += 1
            def success():

                if self.GEL.packet_counter <= self.GEL.TOTAL_PACKET:
                    next_arrival_time = new_event_time + negative_exponential_distribution(self.arrivalRate)
                    next_df = DataFrame("data", next_arrival_time, sender, receiver, self.ackId, self)
                    self.createArrivalDataFrameEvent(next_arrival_time, receiver, "internal DF", next_df, next_df.origin)

                self.createSenseChannelEvent(new_event_time, df, "df, stage 0", df.origin)

            def failure():
                self.buffer.insert_dataframe(df)

            arrival = ArrivalDataFrameEvent(name, new_event_time, sender, receiver, df, success, failure, df.origin)
            self.GEL.addEvent(arrival)

        elif name == "external DF":
            ack_time = event_time
            ack_sender = self
            ack_receiver = df.sender
            ack = DataFrame("ack", ack_time, ack_sender, ack_receiver, df.id, df.origin)

            ack.size = 64

            def success():
                """
                To return an ACK to the sender
                ack_time = event_time
                """
                self.createSenseChannelEvent(ack_time, ack, "ack, stage 0", df.origin)
            def failure():
                """
                No failure
                :return:
                """
                pass

            arrival = ArrivalDataFrameEvent(name, ack_time, sender, receiver, df, success, failure, df.origin)
            self.GEL.addEvent(arrival)

        elif name == "ack":
            success_time = event_time + 0

            def success():
                "to get the unacked event from the notAckedDict and then acknowledge the packet"
                unacked = self.notACKedDict[df.id]
                unacked.ACKed = True

            success_event = successTransferEvent(success_time, df, success, failure, df.origin)
            self.GEL.addEvent(success_event)


    def createSenseChannelEvent(self, event_time: float, df: DataFrame, type: str, origin, counter: float = None):
        """
        five types of sense event
            1) df, stage 0
                success => If the channel is idle, wait for 1 DIFS (0.1 ms)
                failure => If the channel is busy, create a countdown and then create another sense event to reduce the timer to 0.
            2) df, stage 1
                success => If the channel is idle again, transfer the dataframe to the channel immediately
                failure => If the channel is busy, create a countdown and then create another sense event to reduce the timer to 0.
            3) ack, stage 0
                success => If the channel is idle, wait for 1 SIFS (0.1 ms)
                failure => If the channel is busy, create a countdown and then create another sense event to reduce the timer to 0.
            4) ack, stage 1
                success => If the channel is idle again, transfer the ack to the channel immediately
                failure => If the channel is busy, create a countdown and then create another sense event to reduce the timer to 0.
            5) Countdown        (not finished)
        """
        success = None
        failure = None
        event_time = event_time + self.senseTime

        if type == "df, stage 0":
            """
            1) df, stage 0
                success => If the channel is idle, wait for 1 DIFS (0.1 ms)
                failure => If the channel is busy, create a countdown and then create another sense event to reduce the timer to 0.
            """

            def success():
                sense_event_time = event_time + self.DIFS
                self.createSenseChannelEvent(sense_event_time, df, "df, stage 1", df.origin)

            def failure():
                sense_event_time = event_time + self.senseTime
                self.createSenseChannelEvent(sense_event_time, df, "RBA", df.origin)

        elif type == "df, stage 1":
            """
            2) df, stage 1
                success => If the channel is idle again, transfer the dataframe to the channel immediately
                    push_event_time_1 = event_time + transfer delay
                failure => If the channel is busy, create a countdown and then create another sense event to reduce the timer to 0.
                    sense_event_time = event_time + self.senseTime
            """

            def success():
                push_event_time = event_time + df.size / self.channel.rate
                self.createPushToChannelEvent(push_event_time, df)

            def failure():
                sense_event_time = event_time + self.senseTime
                _counter = self.random_backoff(df)
                self.createSenseChannelEvent(sense_event_time, df, "Countdown", _counter)

        elif type == "ack, stage 0":
            """
            3) ack, stage 0
                success => If the channel is idle, wait for 1 SIFS (0.1 ms)
                           sense_time = event_time + 0.1
                failure => If the channel is busy, do nothing
        
            """
            def success():
                sense_event_time = event_time + self.SIFS
                self.createSenseChannelEvent(sense_event_time, df, "ack, stage 1", df.origin)

            def failure():
                pass

        elif type == "ack, stage 1":
            """
            4) ack, stage 1
                success => If the channel is idle again, transfer the ack to the channel immediately
                           push_event_time = event_time + transfer delay
                failure => If the channel is busy, create a countdown and then create another sense event to reduce the timer to 0.
            """

            def success():
                push_event_time = event_time + df.size / self.channel.rate
                self.createPushToChannelEvent(push_event_time, df, "ack")

        elif type == "Countdown":
            """
                5) Countdown        (not finished)
            """


            pass

        sense_event_time = event_time
        senseChannelEvent = SenseChannelEvent(sense_event_time, type, df, success, failure, df.origin )
        self.GEL.addEvent(senseChannelEvent)

    def createPushToChannelEvent(self, event_time:float, df: DataFrame, type:str = "external DF"):
        """
        After we detect the channel is idle again after DF stage 1 or ACK stage 1, we immediately push the packet into the channel
        pushEventTime = event_time + 0

        There are two types of push event. One is external DF and the other is ack
        external DF:
            success => schedule a departure event and then expect an ACK packet return
            failure => no failure would occur

        ack:
            success => just schedule a departure event, no need to schedule an ACK expect event
            failure => no failure

        """

        def success():
            """
            If success, expect an ACK packet return
            departure_event_time = event_time + transmission_time_df + transmission_time_ACK
            expected_ACK_time = event_time + (df size + ack size) / self.channel.rate + self.senseTime * 2 + 1e-9
            1e-9 ensure that the expected_ACK_time must be behind the ACK received time
            :return:
            """
            departure_event_time = event_time + df.size / self.channel.rate

            self.channel.createDepartureEvent(departure_event_time, df, type)

            if type == "external DF":
                expected_ACK_time = event_time + (df.size + 64) / self.channel.rate + self.senseTime * 2 + 1e-9
                self.createExpectAckEvent(expected_ACK_time, df)
            elif type == "ack":
                """do not need to pass back ack if the packet is an ack"""
                pass

        def failure():
            pass

        push_event_time = event_time + 0
        pushEvent = PushToChannelEvent(push_event_time, f"push {df.type} to channel", df, success, failure, df.origin)
        self.GEL.addEvent(pushEvent)



    def createExpectAckEvent(self, event_time: float, df: DataFrame):
        """
        If df is pushed to the channel, the sender expects an ACK packet will come back. This method is to create the AckExpecetedEvent and put it into the GEL.
        If the sender receives the ACK packet before timeout, then it does nothing; otherwise, it retransmit the packet
        success => do nothing
        failure => retransmit the packet (not finished)
        expected_event_time = event_time + total_transmission_time (df and ACK) + SIFS + 2 * senseTime

        """
        expected_event_time = event_time + (df.size + 64) / self.channel.rate + self.SIFS + self.senseTime * 2 + 0.0001


        _ackExpectEvent = AckExpectedEvent(expected_event_time, df, success=None, failure=None, origin = df.origin)

        def success():
            """to remove the object from the unACK Array"""
            del self.notACKedDict[df.id]
            pass
            # del _ackExpectEvent

        def failure():
            """
            to remove the object from the unACK Array
            Then, use the RBA to create a counter and retransmit the object
            """
            df.number_of_collision += 1

            counter = self.random_backoff(df.number_of_collision)
            print(df.number_of_collision, counter)

            self.createSenseChannelEvent(event_time, df, "Countdown", counter)

            del self.notACKedDict[df.id]

        _ackExpectEvent.success = success
        _ackExpectEvent.failure = failure
        _ackExpectEvent._id = df.id
        _ackExpectEvent.ACKed = False

        self.notACKedDict[df.id] = _ackExpectEvent
        self.GEL.addEvent(_ackExpectEvent)


    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self.name)

