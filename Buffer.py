from collections import deque
from DataFrame import DataFrame

class Buffer(object):
    def __init__(self):
        self.array = deque()
        self.number_in_buffer_array = []
        self.number_in_link_processor = 0

    def insert_dataframe(self, df: DataFrame) -> None:
        """
        To insert a packet into the end of a buffer
        :param dataframe:
        """
        self.array.appendleft(df)

    def pop_dataframe(self) -> DataFrame:
        """
        To get the packet at the front of the buffer
        :return:
        """
        dataframe =  self.array.pop()
        return dataframe
