from random import randint

def rba(collision_value):
        LOWER_BOUND = 1
        retval = randint(LOWER_BOUND, (pow(2,collision_value)-1))
        return retval
