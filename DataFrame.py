import random
from Distribution import negative_exponential_distribution
import configparser


class DataFrame(object):
    def __init__(self, type, created_time: float, sender, receiver, id, origin):
        """
        type: ack / data
        created_time: The time the dataframe is created
        """
        self.type = type
        self.sender = sender
        self.receiver = receiver
        self.created_time = created_time
        self.process_time = 0
        self.departure_time = 0
        self.number_of_collision = 0
        self.id = id
        self.origin = origin
        self.fate = "failure"
        self.fate_time = 0

        config = configparser.ConfigParser()
        config.read("configuration_file.ini")
        ARRIVE_RATE = float(config["DEFAULT"]["ARRIVE_RATE"])

        if type == "ACK":
            # acknowledgement frame is constant in size (64 bytes).
            self.size = 64
        elif type == "data":
            # The data frame length(r)(identically distributed for all nodes) is a negativeexponentially distributed random variable in the range 0 < r ≤ 1544 bytes
            size = 10000
            while size > 1544 or size < 0:
                size = negative_exponential_distribution(ARRIVE_RATE)
            self.size = 1000



    def calculate_delay(self):
        return self.departure_time - self.created_time

    def negative_exponential_distribution(rate: float) -> float:
        return (-1/rate) * math.log(1 - random.random())


    def __repr__(self):
        return str(self.global_Id)