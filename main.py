#from configuration_file import NUMBER_OF_HOST
from Host import Host
from Channel import Channel
from Event import ScheduleDataFrameEvent, ProcessDataFrameArrivalEvent
from GEL import Global_Event_List
import json
import configparser

while True:
    try:
        NUMBER_OF_HOST = int(input("Enter number of hosts: "))
        if NUMBER_OF_HOST <= 0:
            print("Error: must be a positive integer")
        else:
            break
    except:
        print("Error: must be a positive integer")

while True:
    try:
        ARRIVE_RATE = float(input("Enter arrival rate: "))
        if ARRIVE_RATE >= 1 or ARRIVE_RATE <= 0:
            print("Error: must be a number between 0 and 1")
        else:
            break
    except:
        print("Error: must be a number between 0 and 1")

config = configparser.ConfigParser()
config.read("configuration_file.ini")
config.set("DEFAULT", "NUMBER_OF_HOST", str(NUMBER_OF_HOST))
config.set("DEFAULT", "ARRIVE_RATE", str(ARRIVE_RATE))

with open('configuration_file.ini', 'w') as configfile:
    config.write(configfile)

gel = Global_Event_List()

for x in gel.host_array:
    initialEvent = ScheduleDataFrameEvent("internal DF", gel.current_time, x, gel.getRandomHost(x), gel)
    gel.addEvent(initialEvent)
        #
    gel_event = True

limited = False
# limited = False
# lower_bound = 17000
# upper_bound = lower_bound + 500

# lower_bound = 112500
# 612 packet problem start

# 10653
lower_bound = 10600

upper_bound = lower_bound + 500
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

                    if x > lower_bound:
                        _o = gel_event.get_event_information()
                        if _o:
                            objects["data"].append(_o)
                        print(gel_event.description())
                        pass
            else:
                break
        for p in gel.packet_array:
            if p.fate == "failure":
                print(f"df {p.global_Id}, {p.fate}")

        json.dump(objects, f)



        average_throughput = gel.calculate_throughput()
        average_delay = gel.calculate_average_network_delay()
        print(f"The average throughput is {average_throughput}, The average_dealy is {average_delay}")

    # prin  t(objects)
else:
    count = 0
    PRINT_ALL = False
    while gel_event:

        gel_event = gel.getNextEvent()

        if gel_event != None:
            gel_event.dataframe.globalID = gel.packet_counter
            gel_event.takeEffect(gel)

            if count % 1 == 0:
                print(gel_event.description())
            count += 1
            # if gel_event.__class__ in  [ScheduleDataFrameEvent, ProcessDataFrameArrivalEvent]  and gel_event.type == "internal DF" or PRINT_ALL:
            # if count % 100 == 0:


            # # print(gel.counter_array)
            # # print(f"==========={count}===========")
            #

    average_throughput = gel.calculate_throughput()
    average_delay = gel.calculate_average_network_delay()
    print(f"The average throughput is {average_throughput}, The average_dealy is {average_delay}")