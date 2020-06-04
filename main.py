from configuration_file import NUMBER_OF_HOST
from Host import Host
from Channel import Channel
from Event import ScheduleDataFrameEvent, ProcessDataFrameArrivalEvent
from GEL import Global_Event_List
import json

gel = Global_Event_List()

for x in gel.host_array:
    initialEvent = ScheduleDataFrameEvent("internal DF", gel.current_time, x, gel.getRandomHost(x), gel)
    gel.addEvent(initialEvent)
        #
    gel_event = True

limited = False
lower_bound = 19
upper_bound = 1000
if limited:
    objects= {
        "host": [],
        "data": []
    }
    objects["host"] = [ h.name for h in gel.host_array ]

    with open("/Users/edwardtang/Project/Cheg/wlan/static/data/output.json", "w") as f:
        for x in range(upper_bound):
            if gel_event != None:
                gel_event = gel.getNextEvent()
                gel_event.dataframe.globalID = gel.packet_counter
                gel_event.takeEffect(gel)

                PRINT_ALL = True

                if gel_event.__class__ in  [ScheduleDataFrameEvent, ProcessDataFrameArrivalEvent]  and gel_event.type == "internal DF" or PRINT_ALL:
                    _o = gel_event.output()
                    if _o:
                        objects["data"].append(_o)
                    if x > lower_bound:
                        print(gel_event.description())
                        pass
            else:
                break
        json.dump(objects, f)

        average_throughput = gel.calculate_throughput()
        average_delay = gel.calculate_average_network_delay()
        print(f"The average throughput is {average_throughput}, The average_dealy is {average_delay}")

    # prin  t(objects)
else:
    count = 0
    while gel_event:

        gel_event = gel.getNextEvent()

        if gel_event != None:
            gel_event.dataframe.globalID = gel.packet_counter
            gel_event.takeEffect(gel)

            PRINT_ALL = True

            if gel_event.__class__ in  [ScheduleDataFrameEvent, ProcessDataFrameArrivalEvent]  and gel_event.type == "internal DF" or PRINT_ALL:

                print(gel_event.description())
                # print(gel.counter_array)
                # print(f"==========={count}===========")
                count+=1

    average_throughput = gel.calculate_throughput()
    average_delay = gel.calculate_average_network_delay()
    print(f"The average throughput is {average_throughput}, The average_dealy is {average_delay}")