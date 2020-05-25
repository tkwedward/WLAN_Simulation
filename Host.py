import Buffer

class Host(object):
    def __init__(self, number):
        self.name = f"Host {number}"
        self.buffer = Buffer()

    def random_backoff(self, dataframe)-> float:
        if n > 10:
            n = 10
        wait_time = random.randint(0, 2 ** n - 1) * 512 / CHANNEL_RATE * 1000
        return wait_time

    def sendACK(self, target):
        pass

    def sense_channel(self) -> str:
        """
        To sense whether the channel is busy or not.
        """
        status = ""
        return status

