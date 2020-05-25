import unittest
from Host import Host
from GEL import Global_Event_List
from Event import ArrivalDataFrameEvent
class MyTestCase(unittest.TestCase):

    def test_arrival_of_data_from_different_host_take_action(self):
        """
        To test if an arrival dataframe event can take effect smoothly
        :return:
        """
        gel = Global_Event_List()

        test_arrival_event = gel.host_array[0].createArrivalDataFrameEvent(gel.host_array[2])
        gel.addEvent(test_arrival_event)

        gel_event = gel.getNextEvent()
        gel_event.takeEffect(gel)   # this is arrival dataframe event
        self.assertEqual(gel_event.name, "Arrival dataframe")

        gel_event_2 = gel.getNextEvent()
        gel_event_2.takeEffect(gel)  # this is sense channel df, stage 0 event
        self.assertEqual(gel_event_2.name, "sense channel, df, stage 0")

        gel_event_3 = gel.getNextEvent() # the channel is idle at beginning, so this event should be sense channel df, stage 1 event
        gel_event_3.takeEffect(gel)
        self.assertEqual(gel_event_3.name, "sense channel, df, stage 1")
        #
        #
        # gel_event_4 = gel.getNextEvent()  # push to channel event
        # self.assertEqual(gel_event_4.name, "Push to Channel")
        # gel_event_4.takeEffect(gel)
        #
        # gel_event_5 = gel.getNextEvent()  # this event should be departure of packet from channel to host 2
        # self.assertEqual(gel_event_5.name, "Departure Event, data")
        # gel_event_5.takeEffect(gel)
        # # this is
        #
        # gel_event_6 = gel.getNextEvent()  # this event should be host 2 receives df from host 0
        # gel_event_6.takeEffect(gel)
        # self.assertEqual(gel_event_6.name, "Arrival_DataFrame, ACK")
        # self.assertEqual([gel_event_6.sender.name, gel_event_6.receiver.name], ["Host 0", "Host 2"])
        #
        #
        # # next event is to return a ACK event
        # gel_event_7 = gel.getNextEvent()
        # print(gel_event_7)
        # self.assertEqual(gel_event_7.name, "sense channel, ACK, stage 0")
        # gel_event_7.takeEffect(gel)
        #
        # gel_event_8 = gel.getNextEvent()
        # self.assertEqual(gel_event_8.name, "sense channel, ACK, stage 1")
        # gel_event_8.takeEffect(gel)
        #
        # gel_event_9 = gel.getNextEvent()
        # self.assertEqual(gel_event_9.name, "Push to Channel")
        # gel_event_9.takeEffect(gel)
        #
        # gel_event_10 = gel.getNextEvent()
        # self.assertEqual(gel_event_10.name, "Departure Event, ACK")
        # gel_event_10.takeEffect(gel)
        #
        # gel_event_11 = gel.getNextEvent()
        # gel_event_11.takeEffect(gel)
        # self.assertEqual(gel_event_11.name, "Arrival_DataFrame, ACK")
        #
        # gel_event_12 = gel.getNextEvent()
        gel.draw_event_timeline()





if __name__ == '__main__':
    unittest.main()