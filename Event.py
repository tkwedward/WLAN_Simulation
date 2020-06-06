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

    def output(self):
        return {}

    def get_counter_information(self):
        GEL = self.origin.GEL
        host_list = GEL.host_array
        counter_dict = { host.name: [] for host in host_list}
        for counter in GEL.counter_array:
            counter_dict[counter.origin.name] = counter.name
        return counter_dict


    def get_buffer_information(self):
        host_array = self.origin.GEL.host_array
        buffer_dict = {}
        for host in host_array:
            buffer_text_array = []

            buffer = host.buffer.array
            # print(buffer)
            for df in buffer:
                df_name = "df " + str(df.global_Id)
                buffer_text_array.append(df_name)
            buffer_dict[host.name] = ", ".join(buffer_text_array)

        return buffer_dict

    def get_blocking_information(self):
        host_array = self.origin.GEL.host_array
        host_blocking_status = {x.name: x.status for x in host_array}
        return host_blocking_status

    def get_host_information(self):
        host_array = self.origin.GEL.host_array
        host_status = {x.name: x.status for x in host_array}
        return host_status

    def get_processing_dataframe_information(self):
        host_array = self.origin.GEL.host_array
        try:
            host_processing_dataframe = {x.name: x.processing_dataframe.global_Id for x in host_array}
            return host_processing_dataframe
        except:
            host_processing_dataframe = {x.name: "" for x in host_array}
            return host_processing_dataframe

    def get_event_information(self):
        result = self.output()
        result["event_list"] = self.origin.GEL.show_event_list()
        result["host_status"] = self.get_host_information()
        result["buffer_status"] = self.get_buffer_information()
        result["counter_status"] = self.get_counter_information()
        result["blocking_status"] = self.get_blocking_information()
        result["processing_dataframe"] = self.get_processing_dataframe_information()
        # print(result["buffer_status"], result["counter_status"])

        return result

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__

    def tell_me_event_name(self):
        return f"{self.__class__.__name__} ({self.origin.name}, df {self.dataframe.global_Id}) (at {self.event_time})"

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
        self.result_description = ""

        if self.type == "internal DF":
            """
            The origin of an internal DF is the sender
            The origin of an external DF is the origin of the df
            The origin of an ack is the origin of the df
            """

            arrival_time = event_time + negative_exponential_distribution(ARRIVE_RATE)
            df = DataFrame("data", arrival_time, self.sender, self.receiver, self.sender.ackId, origin=self.origin)
            df.global_Id = self.GEL.packet_counter
            df.ACKed = False
            self.arrival_time = arrival_time
            self.dataframe = df
            self.GEL.packet_counter += 1
            self.GEL.packet_array.append(df)
            self.sender.ackId += 1


            def success():
                # if self.GEL.packet_counter < self.GEL.TOTAL_PACKET:
                #     new_arrival_event = ScheduleDataFrameEvent(_type, event_time, sender, receiver, self.GEL, sender)
                #     # self.GEL.addEvent(new_arrival_event)

                self.sender.processArrivalDataFrame(arrival_time, self.receiver, "internal DF", df, df.origin)


            arrival_Event = ProcessDataFrameArrivalEvent(self.type, arrival_time, self.sender, self.receiver, df)
            arrival_Event.success = success
            self.arrival_time +=  0.00000001

            self.GEL.addEvent(arrival_Event)

        elif self.type == "external DF":
            arrival_time = event_time + 0.00000001
            self.arrival_time = arrival_time
            self.dataframe = df

            def success():
                self.sender.processArrivalDataFrame(arrival_time, self.receiver, "external DF", df, df.origin)


            arrival_Event = ProcessDataFrameArrivalEvent(self.type, arrival_time, self.sender, self.receiver, df)
            arrival_Event.success = success
            self.GEL.addEvent(arrival_Event)

        elif self.type == "ack":
            arrival_time = event_time + 0.00000001
            original_sender = self.sender
            original_receiver = self.receiver
            self.sender = original_receiver
            self.receiver = original_sender
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
        # self.success()


    def description(self):
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), Schedule Dataframe {self.type} (at {self.arrival_time}, from {self.sender} to {self.receiver})s, {self.event_time} ms"

    def output(self):
        return {
                "event": self.__class__.__name__,
                "event_time": self.event_time,
                "event_id": self.event_id,
                "dataframe_id": self.dataframe.global_Id,
                "dataframe_type": self.type,
                "origin": self.origin.name,
                "type": self.type,
                "arrival_time": self.arrival_time,
                "sender": self.sender.name,
                "receiver": self.receiver.name,
                "result_description": self.result_description,
                "channel_status": self.sender.GEL.channel.status
        }

    def __repr__(self):
        return f"{self.__class__.__name__} ({self.origin.name})"



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

        if sender.status == "idle" or self.dataframe.type == "ack":
            self.success()
            self.result_description = f"{self.type} arrives and it is processed now"
        else:
            self.sender.buffer.insert_dataframe(self.dataframe)
            self.result_description = f"{self.type} arrives but is is buffered because the host is busy"
            self.failure()

    def description(self):
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), sender = {self.sender}, receiver = {self.receiver}, {self.result_description}, {self.event_time} ms"

    def output(self):
        return {
                "event": self.__class__.__name__,
                "event_time": self.event_time,
                "event_id": self.event_id,
                "dataframe_id": self.dataframe.global_Id,
                "dataframe_type": self.type,
                "origin": self.origin.name,
                "type": self.type,
                "sender": self.sender.name,
                "receiver": self.receiver.name,
                "result_description": self.result_description,
                "channel_status": self.sender.GEL.channel.status
        }


    def __str__(self):
        return f"{self.type}  {self.origin}, {self.sender}, {self.receiver}"

    def __repr__(self):
        return f"{self.__class__.__name__} ({self.type}  {self.origin}, {self.sender}, {self.receiver})"



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
        self.origin.status == "busy"
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time
        if gel.channel.status == "idle":
            self.result = "success"
            self.success()
        else:
            create_counter_result = self.failure()
            self.result = "failure"
            if create_counter_result:
                counter = create_counter_result[0]
                result_text = create_counter_result[1][1]
                self.result_description.append(f"Timer {counter.global_Id} for {self.dataframe.global_Id} is created, and it will be ready at {counter.finish_time}")
                self.result_description.append(result_text)


    def output(self):
        return {
                "event": self.__class__.__name__,
                "event_time": self.event_time,
                "event_id": self.event_id,
                "dataframe_id": self.dataframe.global_Id,
                "dataframe_type": self.type,
                "origin": self.origin.name,
                "type": self.type,
                "sender": self.dataframe.sender.name,
                "receiver": self.dataframe.receiver.name,
                "result": self.result,
                "result_description": self.result_description,
                "channel_status": self.origin.GEL.channel.status
        }

    def description(self):

        return_text = f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}), sense channel ({self.origin.GEL.channel.status}, happen at {self.dataframe.sender}), {self.type}, {self.event_time} ms"
        # print("-----", self.result_description)
        return_text = self.combine_return_text(return_text, self.result_description)
        return return_text

    def __repr__(self):
        return f"{self.__class__.__name__} ({self.dataframe.name}  {self.origin}, {self.event_time})"

    def tell_me_event_name(self):
        return f"{self.__class__.__name__}, {self.type} ({self.origin.name, self.dataframe.global_Id}) (at {self.event_time})"


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
        return_text = f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}, happen at {self.origin}), PushToChannelEvent, {self.event_time} ms"
        self.combine_return_text(return_text, self.result_description)
        return return_text


    def output(self):
        return {
                "event": self.__class__.__name__,
                "event_time": self.event_time,
                "event_id": self.event_id,
                "dataframe_id": self.dataframe.global_Id,
                "push_type": self.type,
                "origin": self.origin.name,
                "type": self.type,
                "sender": self.dataframe.sender.name,
                "receiver": self.dataframe.receiver.name,
                "result_description": self.result_description,
                "channel_status": self.origin.GEL.channel.status
        }

class DepartureEvent(Event):
    def __init__(self, event_time, df, success, failure, origin):
        super().__init__(event_time)
        self.type = df.type
        self.dataframe = df
        self.success = success
        self.failure = failure
        self.origin = origin
        self.result_description = []

    def description(self):
        return_text = f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}, happen at channel), Departure Event, {self.dataframe.type}, {self.event_time} ms"
        return_text = self.combine_return_text(return_text, self.result_description)
        return return_text

    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time
        if gel.channel.status == "busy":
            gel.channel.change_status(gel.current_time)


            for counter in gel.counter_array:
                reschedule_result = counter.reschedule_finish_time(gel.current_time)
                new_counter_timeout_event = reschedule_result[0]
                self.result_description = reschedule_result[1]
                gel.addEvent(new_counter_timeout_event)

            self.success()
        else:
            # pass to discard the item
            self.failure()

    def output(self):
        return {
                "event": self.__class__.__name__,
                "event_time": self.event_time,
                "event_id": self.event_id,
                "dataframe_id": self.dataframe.global_Id,
                "departure_type": self.type,
                "origin": self.origin.name,
                "type": self.type,
                "sender": self.dataframe.sender.name,
                "receiver": self.dataframe.receiver.name,
                "channel_status": self.origin.GEL.channel.status,
                "result_description": self.result_description
        }


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

    def description(self):
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}, happen at {self.origin}), I am Expecting an Ack from the receiver at {self.expected_time}, {self.dataframe.type}, {self.event_time} ms "

    def output(self):
        return {
                "event": self.__class__.__name__,
                "event_time": self.event_time,
                "expected_time": self.expected_time,
                "event_id": self.event_id,
                "dataframe_id": self.dataframe.global_Id,
                "departure_type": self.type,
                "origin": self.origin.name,
                "type": self.type,
                "sender": self.dataframe.sender.name,
                "receiver": self.dataframe.receiver.name,
                "channel_status": self.origin.GEL.channel.status
        }

class SuccessTransferEvent(Event):
    def __init__(self, event_time, df, success, failure, origin):
        super().__init__(event_time+1e-11)
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

        self.dataframe.origin.processing_dataframe.ACKed = True

        if len(self.origin.buffer.array) > 0:
            print(f"=================sucess transfer {self.origin.processing_dataframe}, {self.dataframe}")

            next_packet = self.origin.buffer.pop_dataframe()
            self.origin.processing_dataframe = next_packet
            self.origin.createSenseChannelEvent(self.origin.GEL.current_time, next_packet, "df, stage 0", self)
            # print(self.origin.GEL.show_event_list())
        self.success()


    def description(self):
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}, happen at {self.origin}s), {self.type}, {self.dataframe.type}, {self.event_time} ms"

    def output(self):
        return {
                "event": self.__class__.__name__,
                "event_time": self.event_time,
                "event_id": self.event_id,
                "dataframe_id": self.dataframe.global_Id,
                "departure_type": self.type,
                "origin": self.origin.name,
                "type": self.type,
                "sender": self.dataframe.sender.name,
                "receiver": self.dataframe.receiver.name,
                "channel_status": self.origin.GEL.channel.status
        }

class AckResultEvent(Event):
    def __init__(self, event_time, df, origin, ackExpectEvent, failure):
        super().__init__(event_time)
        self.dataframe = df
        self.origin = origin
        self.ackExpectEvent = ackExpectEvent
        self.failure = failure
        self.counter_duration = None

    def takeEffect(self, gel):
        self.event_id = len(gel.timeLineEvent)
        gel.current_time = self.event_time

        # target_event = self.origin.findExpectEvent(self.dataframe.global_Id)
        # del target_event


        if self.ackExpectEvent.ACKed == True or self.dataframe.ACKed == True:
        # if self.ackExpectEvent.ACKed == True:
            self.dataframe.fate = "success"

            self.dataframe.fate_time = self.event_time
            self.result = "success"
            self.status = "idle"


            # if len(self.origin.buffer.array)!=0:
            #     next_packet = self.origin.buffer.pop_dataframe()
            #     self.origin.processing_dataframe = next_packet.name
            #     self.origin.createSenseChannelEvent(gel.current_time, next_packet, "df, stage 0", self.origin)

        else:
            print("========", self.dataframe)
            self.dataframe.fate = "failure"
            self.result = "failure"
            self.counter_duration = self.failure()

            # self.origin.createSenseChannelEvent(self.event_time, self.dataframe, "df, stage 0", self.dataframe.origin)

    def description(self):
        if self.result == "success":
            description = "success to get back the ack packet"
        else:
            description = f"failure to get back the ack packet. Collision happened. I will do RBA and retransmit the dataframe again at {self.counter_duration}."
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}, happen at {self.origin}), Expected ACK timeout. Result: {description}, {self.event_time} ms"

    def output(self):
        return {
                "event": self.__class__.__name__,
                "event_time": self.event_time,
                "event_id": self.event_id,
                "dataframe_id": self.dataframe.global_Id,
                "origin": self.origin.name,
                "sender": self.dataframe.sender.name,
                "receiver": self.dataframe.receiver.name,
                "result": self.result,
                "counter_duration": self.counter_duration,
                "channel_status": self.origin.GEL.channel.status
        }


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
            self.origin.blocking = False
            self.origin.createPushToChannelEvent(self.event_time, self.dataframe, "external DF")

            gel.counter_array = list(filter(lambda x: x.global_Id != self.global_Id, gel.counter_array))

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
        return f"{self.event_id}, ({self.origin}, global packet Id = {self.dataframe.global_Id}, happen at {self.origin}), {result}, {self.event_time} ms"

    def output(self):
        return {
                "event": self.__class__.__name__,
                "event_time": self.event_time,
                "event_id": self.event_id,
                "dataframe_id": self.dataframe.global_Id,
                "origin": self.origin.name,
                "sender": self.dataframe.sender.name,
                "receiver": self.dataframe.receiver.name,
                "status": self.status,
                "channel_status": self.origin.GEL.channel.status
        }

