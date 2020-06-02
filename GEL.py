from DataFrame import DataFrame
from Channel import Channel
from Buffer import Buffer
from Host import Host
from Distribution import negative_exponential_distribution
from Event import Event
import random
from collections import deque

class Global_Event_List(object):
    def __init__(self, ARRIVE_RATE = 0.1, SERVICE_RATE = 11e6, TOTAL_PACKET=1000, NUMBER_OF_HOST = 10):
        self.channel = Channel(SERVICE_RATE, self)
        self.host_array = [ Host(n, self) for n in range(NUMBER_OF_HOST) ]
        self._previousEvent = None

        # constants
        self.ARRIVE_RATE = ARRIVE_RATE
        self.SERVICE_RATE = SERVICE_RATE
        self.TOTAL_PACKET = TOTAL_PACKET

        # variables and counters
        self.timeLineEvent = []
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

    #
    # def arrival_time(self)->float:
    #     """
    #     To calculate the arrival time of the next arrival packet
    #     """
    #     return self.current_time + negative_exponential_distribution(self.ARRIVE_RATE)
    #
    # def transmit_time(self)->float:
    #     """
    #     To calculate the transfer time of a packet in the link processor
    #     """
    #     return self.current_time + negative_exponential_distribution(self.SERVICE_RATE)
    #

    #
    # def initialFirstEvent(self) -> None:
    #     """
    #     Initialize the simulation by creating an initial arrival event and packet
    #     :return:
    #     """
    #     _event_time = self.arrival_time()
    #     _event = Event("Arrival", _event_time)
    #     _packet = self.create_packet()
    #     _event.packet = _packet
    #     self.addEvent(_event)
    #
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

    def getRandomHost(self, initializer):
        result_list = list(filter(lambda x: x!= initializer, self.host_array))
        target_num = random.randint(0, len(result_list)-1)
        return result_list[target_num]


    def __repr__(self):
        _event_list = [f"{event}, {event.event_time}" for event in self.event_list]
        return ", ".join(_event_list)
    #
    # def get_total_time(self) -> float:
    #     return self.timeLineEvent[-1].event_time
    #
    #
    # def getNumberInSystem(self)-> int:
    #     # to get the number of packets in the system at that moment
    #     return self.buffer.number_in_link_processor + len(self.buffer.array)
    #
    # def mean_number_in_system(self)-> float:
    #     """
    #     in self.number_in_system, it contains the number of packets in the system when the event is about to happen.
    #     This function calculate the area in each time interval, and then add them together.
    #     :return: the mean number in the system
    #     """
    #     total_number_array = [x["number_in_system"] * x["time_duration"] for x in self.number_in_system]
    #     total_area = sum(total_number_array)
    #     return total_area/self.current_time
    #
    def draw_event_timeline(self)-> None:
        """
        To Draw all the events in in the timeLineEvent array
        :return:
        """
        # timelineText = []
        for i, event in enumerate(self.timeLineEvent):
            # timelineText.append(f"{i}. {event.name}")
            print(f"{i+1}. {event.description()}")


    def calculate_throughput(self) -> float:
        total_bytes_transferred = 0
        for event in self.timeLineEvent: # find total number of bytes transferred in simulation
            if event.type == "success transfer":
                total_bytes_transferred += event.df.size

        total_simulation_time = self.timeLineEvent[-1].event_time

        return total_bytes_transferred/total_simulation_time


    def calculate_average_network_delay(self) -> float:
        trans_and_queueing_delay = 0
        queued_events = {}
        for event in self.timeLineEvent:    # keep track of scheduled dataframe departures
            if event.type == "internal DF":
                queued_events[event.df] = event.event_time
            elif isinstance(event, DepartureEvent): # measure time from scheduled departure to actual departure (queueing and transmission delay)
                scheduled_time = queued_events[event.df]
                trans_and_queueing_delay += (event.event_time - scheduled_time)

        throughput = calculate_throughput()

        return trans_and_queueing_delay / throughput

    #
    #
    # def statistic(self)-> None:
    #     """
    #     To get the statistics
    #     Not finished
    #     :return:
    #     """
    #
    #     print("Event Timeline")
    #     self.draw_event_timeline()
    #     print("======"*10)
    #     print("dropped number")
    #     print(f"The number of dropped packet is {self.buffer.get_dropped_packet_number()}")
    #     print("======" * 10)
    #     print("Utilization time data")
    #     total_time = self.get_total_time()
    #     busy_time = self.link_processor.get_busy_time()
    #     print(f"The total time is {total_time}, the busy time is {busy_time}")
    #     print(f"The percentage of busy time is {round(busy_time / total_time * 100, 2)}%")
    #     print("======" * 10)
    #     print(f"The mean number of packet in the system is {self.mean_number_in_system()}")
    #     # print(f"The number of mean queue length is {self.buffer.mean_queue_length()}")
    #     print("======" * 10)
    #     rho = self.ARRIVE_RATE / self.SERVICE_RATE
    #     print(f"The value of rho is {rho}")
    #     print(f"The theoretical value of number in the system is {rho/(1-rho)}")
    #
    #
    #

