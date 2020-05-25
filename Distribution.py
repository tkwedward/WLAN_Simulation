import math
import random
from configuration_file import CHANNEL_RATE

def negative_exponential_distribution(rate: float) -> float:
    return (-1/rate) * math.log(1 - random.random())
