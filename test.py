import unittest
from Host import Host
from GEL import Global_Event_List
from Event import ArrivalDataFrameEvent
class MyTestCase(unittest.TestCase):

    def test_successful_transfer_cycle_without_RBA(self):
        """
        To test if an arrival dataframe event can take effect smoothly
        :return:
        """
        gel = Global_Event_List()

        # initialize the event
        gel.host_array[0].createArrivalDataFrameEvent(gel.current_time, gel.host_array[2], "internal DF")

        gel_event_1 = gel.getNextEvent()
        gel_event_1.takeEffect(gel)
        self.assertEqual(gel_event_1.name, "internal DF")

        gel_event_2 = gel.getNextEvent()
        gel_event_2.takeEffect(gel)
        self.assertEqual(gel_event_2.name, "sense channel, df, stage 0")

        gel_event_3 = gel.getNextEvent()
        gel_event_3.takeEffect(gel)
        self.assertEqual(gel_event_3.name, "sense channel, df, stage 1")

        gel_event_4 = gel.getNextEvent()
        gel_event_4.takeEffect(gel)
        self.assertEqual(gel_event_4.name, "push data to channel")

        gel_event_5 = gel.getNextEvent()
        gel_event_5.takeEffect(gel)
        self.assertEqual(gel_event_5.name, "Departure Event, data")

        # Host 2 receive the packet from Host 1
        gel_event_6 = gel.getNextEvent()
        gel_event_6.takeEffect(gel)
        self.assertEqual(gel_event_6.name, "external DF")

        # Host 2 sense if the channel is idle or not
        gel_event_7 = gel.getNextEvent()
        gel_event_7.takeEffect(gel)
        self.assertEqual(gel_event_7.name, "sense channel, ack, stage 0")

        gel_event_8 = gel.getNextEvent()
        gel_event_8.takeEffect(gel)
        self.assertEqual(gel_event_8.name, "sense channel, ack, stage 1")

        gel_event_9 = gel.getNextEvent()
        gel_event_9.takeEffect(gel)
        self.assertEqual(gel_event_9.name, "push ack to channel")

        gel_event_10 = gel.getNextEvent()
        gel_event_10.takeEffect(gel)
        self.assertEqual(gel_event_10.name, "Departure Event, ack")

        gel_event_11 = gel.getNextEvent()
        gel_event_11.takeEffect(gel)
        self.assertEqual(gel_event_11.name, "success transfer")


        # gel.draw_event_timeline()







if __name__ == '__main__':
    unittest.main()