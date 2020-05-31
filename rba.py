from random import randint

FACTOR = 512
LOWER_BOUND = 0

def rba(collision_value):
        retval = FACTOR * randint(LOWER_BOUND, (pow(2,collision_value)-1))
        return retval



