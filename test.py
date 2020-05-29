import unittest
from Host import Host
from GEL import Global_Event_List
from Event import ProcessDataFrameArrivalEvent, ScheduleDataFrameEvent
class MyTestCase(unittest.TestCase):

    def test_successful_transfer_cycle_without_RBA(self):
        """
        To test if an arrival dataframe event can take effect smoothly
        :return:
        """
        gel = Global_Event_List()
        initialEvent = ScheduleDataFrameEvent("internal DF", gel.current_time, gel.host_array[0], gel.host_array[2], gel)
        gel.addEvent(initialEvent)

        # initialize the event
        gel_event_1 = gel.getNextEvent()
        gel_event_1.takeEffect(gel)
        # self.assertEqual(gel_event_1.name, "internal DF")

        gel_event_2 = gel.getNextEvent()
        gel_event_2.takeEffect(gel)
        # self.assertEqual(gel_event_2.name, "sense channel, df, stage 0")

        gel_event_3 = gel.getNextEvent()
        gel_event_3.takeEffect(gel)
        # self.assertEqual(gel_event_3.name, "sense channel, df, stage 1")

        gel_event_4 = gel.getNextEvent()
        gel_event_4.takeEffect(gel)
        # # self.assertEqual(gel_event_4.name, "push data to channel")
        #
        gel_event_5 = gel.getNextEvent()
        gel_event_5.takeEffect(gel)
        # # self.assertEqual(gel_event_5.name, "Departure Event, data")
        #
        # # Host 2 receive the packet from Host 1
        gel_event_6 = gel.getNextEvent()
        gel_event_6.takeEffect(gel)
        # # self.assertEqual(gel_event_6.name, "external DF")
        #
        # # Host 2 sense if the channel is idle or not
        gel_event_7 = gel.getNextEvent()
        gel_event_7.takeEffect(gel)
        # # self.assertEqual(gel_event_7.name, "sense channel, ack, stage 0")
        #
        gel_event_8 = gel.getNextEvent()
        gel_event_8.takeEffect(gel)
        # # self.assertEqual(gel_event_8.name, "sense channel, ack, stage 1")
        #
        gel_event_9 = gel.getNextEvent()
        gel_event_9.takeEffect(gel)
        # # self.assertEqual(gel_event_9.name, "push ack to channel")
        #
        gel_event_10 = gel.getNextEvent()
        gel_event_10.takeEffect(gel)
        # # self.assertEqual(gel_event_10.name, "Departure Event, ack")
        #
        gel_event_11 = gel.getNextEvent()
        gel_event_11.takeEffect(gel)
        # self.assertEqual(gel_event_11.name, "success transfer")
        # gel.draw_event_timeline()
    #
    #

    def test_successful_transfer_TOTAL_PACKET_for_One_HOST(self):
        gel = Global_Event_List()
        gel.TOTAL_PACKET = 5
        initialEvent = ScheduleDataFrameEvent("internal DF", gel.current_time, gel.host_array[0], gel.host_array[2], gel)
        gel.addEvent(initialEvent)

        while gel.packet_counter <= gel.TOTAL_PACKET:
            # print(gel.packet_counter)
            gel_event = gel.getNextEvent()
            if gel_event == None:
                break
            else:
                gel_event.takeEffect(gel)
        # gel.draw_event_timeline()
        # self.assertEqual(gel_event_11.name, "success transfer")

    def test_successful_transfer_TOTAL_PACKET_for_TWO_HOST(self):
        gel = Global_Event_List()
        gel.TOTAL_PACKET = 20
        for x in gel.host_array:
            initialEvent = ScheduleDataFrameEvent("internal DF", gel.current_time, x, gel.getRandomHost(x), gel)
            gel.addEvent(initialEvent)
        #
        # num = 100
        # for x in range(0, num):
        #     gel_event = gel.getNextEvent()
        #     gel_event.dataframe.globalID = gel.packet_counter
        #     print(gel_event)
        #     gel_event.takeEffect(gel)
        #
        # gel.draw_event_timeline()

        gel_event = True
        try:
            while gel_event:
                gel_event = gel.getNextEvent()
                gel_event.dataframe.globalID = gel.packet_counter
                gel_event.takeEffect(gel)

        except Exception as e:
            gel.draw_event_timeline()
            print(e)





if __name__ == '__main__':
    unittest.main()