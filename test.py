import unittest
from Host import Host
from GEL import Global_Event_List
from Event import ProcessDataFrameArrivalEvent, ScheduleDataFrameEvent, AckResultEvent
class MyTestCase(unittest.TestCase):
    #
    def test_successful_transfer_cycle_without_RBA(self):
        """
        To test if an arrival dataframe event can take effect smoothly
        :return:
        """
        gel = Global_Event_List()
        for x in gel.host_array[0:2]:
            initialEvent = ScheduleDataFrameEvent("internal DF", gel.current_time, x, gel.getRandomHost(x), gel)
            gel.addEvent(initialEvent)

        # initialize the event
        """
        Timer 1 for 1 is created, and it will be ready at 1.2062966341753119
        Timer 1 will ring at 1.2142218689806692


        """
        event_run = 100
        start_at =40
        for x in range(event_run):
            gel_event_11 = gel.getNextEvent()
            gel_event_11.takeEffect(gel)
            if x > start_at-2:
                print(gel_event_11.description())
        self.assertEqual(gel_event_11.name, "success transfer")

    def test_successful_transfer_TOTAL_PACKET_for_One_HOST(self):
        gel = Global_Event_List()
        for x in gel.host_array[0:1]:
            initialEvent = ScheduleDataFrameEvent("internal DF", gel.current_time, x, gel.getRandomHost(x), gel)
            gel.addEvent(initialEvent)

        while gel.packet_counter <= gel.TOTAL_PACKET:
            # print(gel.packet_counter)
            gel_event = gel.getNextEvent()

            if gel_event == None:
                break
            else:
                gel_event.takeEffect(gel)
                print(gel_event.description())
        gel.draw_event_timeline()
        self.assertEqual(gel_event_11.name, "success transfer")





if __name__ == '__main__':
    unittest.main()