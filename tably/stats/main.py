import sys, os, itertools, math

from .. import builder
from . import stats_adv as adv

def len_of(values):
    values = list(val for val in values if val != builder.MISSING)
    return len(values)

def min_of(values):
    values = list(val for val in values if val != builder.MISSING)
    if len(values):
        return min(values)
    else:
        return builder.MISSING

def max_of(values):
    values = list(val for val in values if val != builder.MISSING)
    if len(values):
        return max(values)
    else:
        return builder.MISSING

def sum_of(values):
    values = list(val for val in values if val != builder.MISSING)
    if len(values):
        return sum(values)
    else:
        return builder.MISSING

def average(values):
    values = list((val for val in values if val != builder.MISSING))
    if len(values):
        return sum(values)/float(len(values))
    else:
        return builder.MISSING

def median(values):
    values = list((val for val in values if val != builder.MISSING))
    medindex_root = len(values)/2.0
    medindex1 = math.floor(medindex_root)
    medindex2 = math.ceiling(medindex_root)
    return average([medindex1,medindex2])

def stdev(values):
    values = list((val for val in values if val != builder.MISSING))
    return adv.lstdev(values)

def most_common(values):
    values = list((val for val in values if val != builder.MISSING))
    return max(set(values), key=values.count)

def least_common(values):
    values = list((val for val in values if val != builder.MISSING))
    return min(set(values), key=values.count)
