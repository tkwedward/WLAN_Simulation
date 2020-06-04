from Event import TimeoutEvent


class Counter(object):
    def __init__(self, created_time, duration, df, origin, gel):
        self.created_time = created_time
        self.finish_time = created_time + duration
        self.dataframe = df
        self.origin = origin
        self.global_Id = df.global_Id
        self.remaining_time = duration
        timeout_event = TimeoutEvent(created_time + duration, df, origin, df.global_Id)
        self.event = timeout_event

        gel.addEvent(timeout_event)


    def freeze(self, current_time):
        """
        To calculate the remaining time so that when the channel's status
        :param current_time:
        :return: None
        """
        self.remaining_time = self.finish_time - current_time
        self.event.status = "deactivate"

        freeze_text_result = f"Timer {self.global_Id} is freezed at {current_time}"

        return self.remaining_time, freeze_text_result

    def reschedule_finish_time(self, current_time):
        """
        When the channel becomes idle again, then reschedule the counter.
        :param current_time:
        :return:
        """

        description_array = []
        new_finish_time = current_time + self.remaining_time

        self.finish_time = new_finish_time
        new_event = TimeoutEvent(new_finish_time, self.event.dataframe, self.event.dataframe.origin, self.event.dataframe.global_Id)
        self.event = new_event
        description_array.append(f"The current time is {current_time}")
        description_array.append(f"Timer {self.global_Id} will ring at {new_finish_time}")
        return new_event, description_array

