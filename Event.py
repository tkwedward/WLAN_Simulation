from DataFrame import DataFrame
from Distribution import negative_exponential_distribution
from configuration_file import ARRIVE_RATE, CHANNEL_RATE

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

    def combine_return_text(self, text0, text_array):
        for x in text_array:
            text0 += f"\n \t {x}"
        return text0

    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time
        if gel.channel.status == "idle":
            self.success()
        else:
            self.failure()

    def __str__(self):
        return "Event"

    def __repr__(self):
        return "Event"

class ScheduleDataFrameEvent(Event):
    """
    just put the item into the GEL, no other function
    """
    def __init__(self, _type, event_time, sender, receiver, gel, origin=None, df=None):
        self.type = _type
        self.event_time = event_time
        self.sender = sender
        self.receiver = receiver
        if origin == None:
            self.origin = sender
        else:
            self.origin = origin
        self.GEL = gel
        self.dataframe = df

        if self.type == "internal DF":
            """
            The origin of an internal DF is the sender
            The origin of an external DF is the origin of the df
            The origin of an ack is the origin of the df
            """

            arrival_time = event_time + negative_exponential_distribution(ARRIVE_RATE)
            df = DataFrame("data", arrival_time, self.sender, self.receiver, self.sender.ackId, origin=self.origin)
            df.global_Id = self.GEL.packet_counter
            self.arrival_time = arrival_time
            self.dataframe = df
            self.GEL.packet_counter += 1
            self.sender.ackId += 1


            def success():
                if self.GEL.packet_counter < self.GEL.TOTAL_PACKET:
                    new_arrival_event = ScheduleDataFrameEvent(_type, event_time, sender, receiver, self.GEL, sender)
                    self.GEL.addEvent(new_arrival_event)

                self.sender.processArrivalDataFrame(arrival_time, self.receiver, "internal DF", df, df.origin)


            arrival_Event = ProcessDataFrameArrivalEvent(self.type, arrival_time, self.sender, self.receiver, df)
            arrival_Event.success = success


            self.GEL.addEvent(arrival_Event)

        elif self.type == "external DF":
            arrival_time = event_time
            self.arrival_time = arrival_time
            self.dataframe = df

            def success():
                self.sender.processArrivalDataFrame(arrival_time, self.receiver, "external DF", df, df.origin)


            arrival_Event = ProcessDataFrameArrivalEvent(self.type, arrival_time, self.sender, self.receiver, df)
            arrival_Event.success = success
            self.GEL.addEvent(arrival_Event)

        elif self.type == "ack":
            arrival_time = event_time

            self.arrival_time = arrival_time
            self.dataframe = df

            def success():
                """
                The sender process the arrived ack, and then
                """
                self.sender.processArrivalDataFrame(arrival_time, self.receiver, "ack", df, df.origin)

            arrival_Event = ProcessDataFrameArrivalEvent(self.type, arrival_time, self.sender, self.receiver, df)
            arrival_Event.success = success
            self.GEL.addEvent(arrival_Event)

    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time
        self.success()


    def description(self):
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), Schedule Dataframe {self.type} (at {self.arrival_time}, from {self.sender} to {self.receiver})s, {self.event_time} ms"


class ProcessDataFrameArrivalEvent(Event):
    def __init__(self, _type, event_time, sender, receiver, df):
        super().__init__(event_time + 0.00000000001)
        self.type = _type
        self.sender = sender
        self.receiver = receiver
        self.dataframe = df
        self.origin = df.origin

    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time
        sender = self.sender

        if self.type == "internal DF":
            if gel.packet_counter < gel.TOTAL_PACKET:

                new_arrival_event = ScheduleDataFrameEvent(self.type, self.event_time, self.sender, self.receiver, gel, self.sender)
                gel.addEvent(new_arrival_event)

        if sender.status == "idle":
            self.success()
            self.result_description = f"{self.type} arrives and it is processed now"
        else:
            self.sender.buffer.insert_dataframe(self.dataframe)
            self.result_description = f"{self.type} arrives but is is buffered because the host is busy"
            self.failure()

    def description(self):
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), sender = {self.sender}, receiver = {self.receiver}, {self.result_description}, {self.event_time} ms"

    def __str__(self):
        return f"{self.type}  {self.origin}, {self.sender}, {self.receiver}"



class SenseChannelEvent(Event):
    def __init__(self, event_time, _type, df, success, failure, origin):
        super().__init__(event_time)
        self.type = _type
        self.dataframe = df
        self.success = success
        self.failure = failure
        self.origin = origin
        self.result_description = []

    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time
        if gel.channel.status == "idle":
            self.success()
        else:
            create_counter_result = self.failure()
            if create_counter_result:
                counter = create_counter_result[0]
                result_text = create_counter_result[1][1]
                self.result_description.append(f"Timer {counter.global_Id} for {self.dataframe.global_Id} is created, and it will be ready at {counter.finish_time}")
                self.result_description.append(result_text)

    def description(self):
        return_text = f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), sense channel ({self.origin.GEL.channel.status}), {self.type}, {self.event_time} ms"
        # print("-----", self.result_description)
        return_text = self.combine_return_text(return_text, self.result_description)
        return return_text

class PushToChannelEvent(Event):
    """
    The df is pushed to channel. Check if the channel is idle or busy
    If idle, then schedule arrival event of the df
    If busy, then discard the event
    """
    def __init__(self, event_time, _type, df, success, failure, origin):
        import inspect

        super().__init__(event_time)
        self.type = _type
        self.dataframe = df
        self.success = success
        self.failure = failure
        self.origin = origin
        self.result_description = []


    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time

        if gel.channel.status == "idle":
            gel.channel.change_status(self.event_time)

            # change into busy mode, then I will freeze all the timers.
            for counter in gel.counter_array:
                freeze_result = counter.freeze(gel.current_time)
                remaining_time = freeze_result[0]
                description_array = freeze_result[1]
                counter.remaining_time = remaining_time
                self.result_description.append(description_array)

            self.success()
        else:
            # pass to discard the item
            self.failure()

    def description(self):
        return_text = f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), PushToChannelEvent, {self.result_description}, {self.event_time} ms"
        self.combine_return_text(return_text, self.result_description)
        return return_text

class DepartureEvent(Event):
    def __init__(self, event_time, df, success, failure, origin):
        super().__init__(event_time)
        self.type = df.type
        self.dataframe = df
        self.success = success
        self.failure = failure
        self.origin = origin
        self.description_array = []

    def description(self):
        return_text = f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), Departure Event, {self.dataframe.type}, {self.event_time} ms"
        return_text = self.combine_return_text(return_text, self.description_array)
        return return_text

    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time
        if gel.channel.status == "busy":
            gel.channel.change_status(gel.current_time)


            for counter in gel.counter_array:
                reschedule_result = counter.reschedule_finish_time(gel.current_time)
                new_counter_timeout_event = reschedule_result[0]
                self.description_array = reschedule_result[1]
                gel.addEvent(new_counter_timeout_event)

            self.success()
        else:
            # pass to discard the item
            self.failure()


class AckExpectedEvent(Event):
    """
    After pushing the df to channel, an ACK is expected to come back
    If ACK is received, then
    """

    def __init__(self, event_time, expected_time, df, origin):
        super().__init__(event_time)
        self.type = "Expect ACK"
        self.dataframe = df
        self.origin = origin
        self.expected_time = expected_time
        self.ACKed = False

    def acknowledge(self):
        self.ACKed = True

    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time
        sender = self.dataframe.sender

        self.success()

    def description(self):
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), I am Expecting an Ack from the receiver at {self.expected_time}, {self.dataframe.type}, {self.event_time} ms "

class SuccessTransferEvent(Event):
    def __init__(self, event_time, df, success, failure, origin):
        super().__init__(event_time)
        self.type = "success transfer"
        self.dataframe = df
        self.success = success
        self.failure = failure
        self.origin = origin
        target_event = df.sender.findExpectEvent(df.global_Id)
        target_event.ACKed = True


    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time
        self.success()

    def description(self):
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), {self.type}, {self.dataframe.type}, {self.event_time} ms"

class AckResultEvent(Event):
    def __init__(self, event_time, df, origin, ackExpectEvent, failure):
        super().__init__(event_time)
        self.dataframe = df
        self.origin = origin
        self.ackExpectEvent = ackExpectEvent
        self.failure = failure

    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time

        target_event = self.origin.findExpectEvent(self.dataframe.global_Id)
        del target_event

        if self.ackExpectEvent.ACKed == True:
            self.result = "success"
            self.status = "idle"


            if len(self.origin.buffer.array)!=0:
                next_packet = self.origin.buffer.pop_dataframe()
                self.origin.createSenseChannelEvent(gel.current_time, next_packet, "df, stage 0", self.origin)
        else:

            self.result = "failure"
            self.counter_duration = self.failure()

            # self.origin.createSenseChannelEvent(self.event_time, self.dataframe, "df, stage 0", self.dataframe.origin)

    def description(self):
        if self.result == "success":
            description = "success to get back the ack packet"
        else:
            description = f"failure to get back the ack packet. Collision happened. I will do RBA and retransmit the dataframe again at {self.counter_duration}."
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), Expected ACK timeout. Result: {description}, {self.event_time} ms"


class TimeoutEvent(Event):
    """
    This event happens when the counter finish counting.
    self.status = when current_time = event_time, check if the status is activated. If it is activated, then the retransmission is successful. If it is deactivated, then just do nothing. The counter object in the GEL will reschedule another TimeOutEvent.
    """
    def __init__(self, event_time, df, origin, global_Id):
        super().__init__(event_time)
        self.dataframe = df
        self.origin = origin
        self.status = "activated"
        self.global_Id = global_Id


    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time
        if self.status == "activated":
            """
            When the counter reaches zero(note that this can only occur while the channel is sensed as being idle), the host transmits the entire frame and then waits for an acknowledgment."""
            self.origin.createPushToChannelEvent(self.event_time, self.dataframe, "external DF")
            try:
                counter = next(filter(lambda x: x.global_Id == self.global_Id, gel.counter_array))
                gel.counter_array.remove(counter)
            except StopIteration:
                pass

        else:
            """
            When the counter is deactivated, do nothing
            """
            pass

    def description(self):
        if self.status == "activated":
            result = "Count down is finished. I am going to push the object to the channel again"
        else:
            result = "The TimeoutEvent is deactivated, I am not going to do anything. The counter will wait for the channel becomes idel again"
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), {result}, {self.event_time} ms"
