from Buffer import Buffer
from DataFrame import DataFrame
from Distribution import negative_exponential_distribution
from Event import ProcessDataFrameArrivalEvent, SenseChannelEvent, PushToChannelEvent, AckExpectedEvent, SuccessTransferEvent, ScheduleDataFrameEvent, AckResultEvent
import random
from Counter import Counter
random.seed(10)

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
        self.notACKedArray = []
        self.ackId = 0

    def rba(self, collision_value):
        if collision_value == 0:
            collision_value = 1
        if collision_value > 10:
            n = 10
        LOWER_BOUND = 1
        retval = random.randint(LOWER_BOUND, (pow(2, collision_value) - 1))
        return retval

    def addToBuffer(self, df: DataFrame):
        self.buffer.append(df)

    def processArrivalDataFrame(self, event_time: float, receiver: "Host", _type: str, df = None, origin = None):
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

        if _type == "internal DF":
            """
            Schedule next event
            To create a sense channel event, or put it into the buffer
            """

            if self.status == "idle":
                self.status = "busy"
                self.createSenseChannelEvent(event_time, df, "df, stage 0", df.origin)



        elif _type == "external DF":
            """
            create an ack packet, and then create a SenseChannel Event for this ack packet 
            """
            ack_time = event_time
            ack = DataFrame("ack", ack_time, df.sender, df.receiver, df.id, df.origin)
            ack.global_Id = df.global_Id
            ack.size = 64

            self.createSenseChannelEvent(event_time, ack, "ack, stage 0", df.origin)

        elif _type == "ack":
            success_time = event_time

            def success():
                "to get the unacked event from the notAckedDict and then acknowledge the packet. If the buffer still contains dataframe, go to sense channel step again for the next dataframe in the buffer"

                if len(self.buffer.array) != 0:
                    next_df = self.buffer.array.popleft()
                    self.createSenseChannelEvent(event_time, next_df, "df, stage 0", df.origin)

            success_event = SuccessTransferEvent(success_time, df, success, failure, df.origin)
            self.GEL.addEvent(success_event)

    def createSenseChannelEvent(self, event_time: float, df: DataFrame, type: str, origin, counter: float = None):
        """
        five types of sense event
            1) df, stage 0
                success => If the channel is idle, wait for 1 DIFS (0.1 ms)
                failure => If the channel is busy, create a countdown and then create another sense event to reduce the timer to 0.
            2) df, stage 1
                success => If the channel is idle again, transfer the dataframe to the channel immediately
                failure => If the channel is busy, create a countdown event
            3) ack, stage 0
                success => If the channel is idle, wait for 1 SIFS (0.1 ms)
                failure => If the channel is busy, do nothing
            4) ack, stage 1
                success => If the channel is idle again, transfer the ack to the channel immediately
                failure => If the channel is busy, do nothing
        """
        success = None
        failure = None
        sense_event_time = event_time + self.senseTime

        if type == "df, stage 0":
            """
            1) df, stage 0
                success => If the channel is idle, wait for 1 DIFS (0.1 ms)
                failure => If the channel is busy, create a countdown and then create another sense event to reduce the timer to 0.
            """

            def success():
                self.createSenseChannelEvent(sense_event_time + self.DIFS, df, "df, stage 1", df.origin)

            def failure():
                self.createSenseChannelEvent(sense_event_time + self.DIFS, df, "df, stage 0", df.origin)

            # def failure_1():
            #     df.number_of_collision += 1
            #     _countDownTime = self.rba(df.number_of_collision)
            #     counter = Counter(sense_event_time, _countDownTime, df, df.origin, self.GEL)
            #     self.GEL.counter_array.append(counter)
            #     description_array = counter.freeze(sense_event_time)
            #
            #     return counter, description_array

        elif type == "df, stage 1":
            """
            2) df, stage 1
                success => If the channel is idle again, transfer the dataframe to the channel immediately
                    push_event_time_1 = event_time + transfer delay
                failure => If the channel is busy, create a countdown and then create another sense event to reduce the timer to 0.
                    sense_event_time = event_time + self.senseTime
            """
            def success():
                push_event_time = sense_event_time
                self.createPushToChannelEvent(push_event_time, df)

            def failure():
                self.createSenseChannelEvent(sense_event_time + self.DIFS, df, "df, stage 0", df.origin)
            #
            # def failure_1():
            #     df.number_of_collision += 1
            #     _countDownTime = self.rba(df.number_of_collision)
            #     counter = Counter(sense_event_time, _countDownTime, df, df.origin, self.GEL)
            #     self.GEL.counter_array.append(counter)
            #     description_array = counter.freeze(sense_event_time)
            #
            #
            #     return counter, description_array

        elif type == "ack, stage 0":
            """
            3) ack, stage 0
                success => If the channel is idle, wait for 1 SIFS (0.1 ms)
                           sense_time = event_time + 0.1
                failure => If the channel is busy, do nothing
        
            """
            def success():
                self.createSenseChannelEvent(sense_event_time + self.SIFS, df, "ack, stage 1", df.origin)

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
                push_event_time = sense_event_time
                self.createPushToChannelEvent(push_event_time, df, "ack")

            def failure():
                pass


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
        self.status = "idle"

        def success():
            """
            If success, expect an ACK packet return
            departure_event_time = event_time + transmission_time_df + transmission_time_ACK
            expected_ACK_time = event_time + (df size + ack size) / self.channel.rate + self.senseTime * 2 + 1e-9
            1e-9 ensure that the expected_ACK_time must be behind the ACK received time
            :return:
            """
            departure_event_time = event_time + df.size / self.channel.rate * 1000
            self.channel.createDepartureEvent(departure_event_time, df, type)


            if type == "external DF":
                self.createExpectAckEvent(event_time, df)

            elif type == "ack":
                """do not need to pass back ack if the packet is an ack"""
                pass

        def failure():
            self.createExpectAckEvent(event_time, df)

        push_event_time = event_time + 0
        pushEvent = PushToChannelEvent(push_event_time, f"push {df.type} to channel", df, success, failure, df.origin)
        self.GEL.addEvent(pushEvent)




    def createExpectAckEvent(self, event_time: float, df: DataFrame):
        """
        If df is pushed to the channel, the sender expects an ACK packet will come back. This method is to create the AckExpecetedEvent and put it into the GEL.
        If the sender receives the ACK packet before timeout, then it does nothing; otherwise, it retransmit the packet
        success => do nothing
        failure => retransmit the packet (not finished)
        expected_event_time = event_time + total_transmission_time (2 df and 2 ACK) + SIFS + 2 * senseTime

        """
        expected_event_time = event_time + (df.size + 64) / self.channel.rate * 1000 + self.senseTime * 2 + self.SIFS + 0.0000001

        ackExpectEvent = AckExpectedEvent(event_time, expected_event_time, df, origin = df.origin)
        ackExpectEvent._id = df.id
        self.notACKedArray.append(ackExpectEvent)

        def failure():
            df.number_of_collision += 1

            if df.number_of_collision > 10:
                df.number_of_collision = 10
            counter_duration = self.rba(df.number_of_collision)

            counter = Counter(expected_event_time, counter_duration, df, self, self.GEL)
            self.GEL.counter_array.append(counter)
            return expected_event_time + counter_duration

        ackResultEvent = AckResultEvent(expected_event_time, df, df.origin, ackExpectEvent, failure)

        self.GEL.addEvent(ackExpectEvent)
        self.GEL.addEvent(ackResultEvent)

    def findExpectEvent(self, global_Id):
        return next(filter(lambda x: x.dataframe.global_Id == global_Id, self.notACKedArray ))

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self.name)