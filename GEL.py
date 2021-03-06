from DataFrame import DataFrame
from Channel import Channel
from Buffer import Buffer
from Host import Host
from Distribution import negative_exponential_distribution
from Event import Event, SuccessTransferEvent, DepartureEvent, ProcessDataFrameArrivalEvent, ScheduleDataFrameEvent
import random
import configparser
from collections import deque

class Global_Event_List(object):
    def __init__(self, ARRIVE_RATE = None, CHANNEL_RATE = None, TOTAL_PACKET=None, NUMBER_OF_HOST = None):
        config = configparser.ConfigParser()
        config.read("configuration_file.ini")
        self.ARRIVE_RATE = float(config["DEFAULT"]["ARRIVE_RATE"])
        self.NUMBER_OF_HOST = int(config["DEFAULT"]["NUMBER_OF_HOST"])
        self.TOTAL_PACKET = int(config["DEFAULT"]["TOTAL_PACKET"])
        self.CHANNEL_RATE = int(config["DEFAULT"]["CHANNEL_RATE"])

        self.channel = Channel(self.CHANNEL_RATE, self)
        self.host_array = [ Host(n, self) for n in range(self.NUMBER_OF_HOST) ]
        self._previousEvent = None

        # variables and counters
        self.timeLineEvent = []
        self.counter_array = []
        self.packet_array = []
        self.event_list = deque()
        self.busy_time = 0
        self.current_time = 0
        self.packet_counter = 0
        self.event_counter = 0

        self.number_in_system = []

    def run_simulator(self, event_show=None)->None:
        """
        To start the simulation
        """
        self.initialFirstEvent()
        self._previousEvent = None

        for i in range(self.TOTAL_PACKET*2):
            next_event = self.getNextEvent()
            if event_show==True:
                print(i, next_event)

            if next_event.name != "Overflow":
                if self._previousEvent!=None:
                    self._previousEvent.nextEvent = next_event
                    next_event.previousEvent = self._previousEvent
                self._previousEvent = next_event


            self.eventTakeAction(next_event)

    def getNextEvent(self) -> Event:
        """
        To get the next event from the event list"""
        self.sort_event_list()
        if len(self.event_list) > 0:
            nextEvent = self.event_list.popleft()
            self.timeLineEvent.append(nextEvent)

            return nextEvent
        else:
            print("no more events")

    def sort_event_list(self) -> None:
        """
        To sort the event list
        """
        try:
            self.event_list = deque(sorted(self.event_list, key=lambda x: x.event_time))
        except:
            print(self.event_list)

    def addEvent(self, event: Event) -> None:
        """
        To add an event to the event list
        :param event:
        :return:
        """
        self.event_list.append(event)
        self.sort_event_list()

    def getRandomHost(self, initializer):
        result_list = list(filter(lambda x: x!= initializer, self.host_array))
        target_num = random.randint(0, len(result_list)-1)
        return result_list[target_num]


    def __repr__(self):
        _event_list = [f"{event}, {event.event_time}" for event in self.event_list]
        return ", ".join(_event_list)

    def show_event_list(self):
        event_list = [_e.tell_me_event_name() for _e in self.event_list]

        return event_list

    def draw_event_timeline_of_packets(self, packet_number=None):
        packets = {}
        for x in range(0, self.packet_counter):
            packets[x] = []

        for event in self.timeLineEvent:
            packet_global_Id = event.dataframe.global_Id
            packets[packet_global_Id].append(event)

        if packet_number == None:
            for x in range(0, self.packet_counter):
                for event in packets[x]:
                    print(event.description())
                print("=" * 100)
        else:
            for event in packets[packet_number]:
                print(event.description())

    def draw_event_timeline(self)-> None:
        """
        To Draw all the events in in the timeLineEvent array
        :return:
        """
        # timelineText = []
        for i, event in enumerate(self.timeLineEvent):
            # timelineText.append(f"{i}. {event.name}")
            print(f" {event.description()}")

    def checkPacket(self, df_number):
        event = next(filter(lambda event: event.dataframe.global_Id == df_number, self.timeLineEvent))
        df = event.dataframe
        # print(f"{df.type}, {df.global_Id}, {df.size}")



    def calculate_throughput(self) -> float:
        """
        To find the throughput of the simulation
        1. Find the total size of successful transferred dataframe
        2. Find the total time of the simulation
        3. throughput = total size / total time
        :return:
        """
        total_bytes_transferred = 0
        for event in self.timeLineEvent: # find total number of bytes transferred in simulation
            if event.__class__ == SuccessTransferEvent:
                total_bytes_transferred += event.dataframe.size

        total_simulation_time = self.timeLineEvent[-1].event_time

        return total_bytes_transferred/total_simulation_time


    def calculate_average_network_delay(self) -> float:
        """
        0. Find the total size of all dataframe
        1. Find out the created time of the dataframe
        2. Find out the time the dataframe is sent to the channel
        3. total delay  = sum of (departure time - created time) of each dataframe
        3. average delay = total delay / total size
        :return:
        """
        trans_and_queueing_delay = 0
        queued_events = {}

        for event in self.timeLineEvent:    # keep track of scheduled dataframe departures
            if event.__class__ == ScheduleDataFrameEvent and event.type == "internal DF":
                queued_events[event.dataframe.global_Id] = event.arrival_time

            elif isinstance(event, DepartureEvent): # measure time from scheduled departure to actual departure (queueing and transmission delay)
                scheduled_time = queued_events[event.dataframe.global_Id]
                trans_and_queueing_delay += (event.event_time - scheduled_time)


        throughput = self.calculate_throughput()

        return trans_and_queueing_delay / throughput
