from configuration_file import NUMBER_OF_HOST
from Host import Host
from Channel import Channel
from Event import ScheduleDataFrameEvent, ProcessDataFrameArrivalEvent
from GEL import Global_Event_List

gel = Global_Event_List()

for x in gel.host_array:
    initialEvent = ScheduleDataFrameEvent("internal DF", gel.current_time, x, gel.getRandomHost(x), gel)
    gel.addEvent(initialEvent)
        #
    gel_event = True


for x in range(1000):
    if gel_event != None:
        gel_event = gel.getNextEvent()
        gel_event.dataframe.globalID = gel.packet_counter
        gel_event.takeEffect(gel)

        PRINT_ALL = True

        if gel_event.__class__ in  [ScheduleDataFrameEvent, ProcessDataFrameArrivalEvent]  and gel_event.type == "internal DF" or PRINT_ALL:
            print(gel_event.description())
#
# while gel_event:
#     gel_event = gel.getNextEvent()
#
#     if gel_event != None:
#         gel_event.dataframe.globalID = gel.packet_counter
#         gel_event.takeEffect(gel)
#
#         PRINT_ALL = True
#
#         if gel_event.__class__ in  [ScheduleDataFrameEvent, ProcessDataFrameArrivalEvent]  and gel_event.type == "internal DF" or PRINT_ALL:
#             print(gel_event.description())

    # gel.draw_event_timeline_of_packets(3)
    # gel.checkPacket(3)

        # gel.draw_event_timeline()
        # for host in gel.host_array:
        #     print(host.buffer.array)


