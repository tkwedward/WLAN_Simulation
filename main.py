#from configuration_file import NUMBER_OF_HOST
from Event import ScheduleDataFrameEvent
from GEL import Global_Event_List
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
    gel_event = True

while gel_event:
    gel_event = gel.getNextEvent()
    if gel_event != None:
        gel_event.dataframe.globalID = gel.packet_counter
        gel_event.takeEffect(gel)
        print(gel_event.description())

average_throughput = gel.calculate_throughput()
average_delay = gel.calculate_average_network_delay()
print(f"The average throughput is {average_throughput}, The average_dealy is {average_delay}")