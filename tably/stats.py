import sys, os, itertools, math

def average(values):
    return sum(values)/float(len(values))

def median(values):
    medindex_root = len(values)/2.0
    medindex1 = math.floor(medindex_root)
    medindex2 = math.ceiling(medindex_root)
    return average([medindex1,medindex2])

def stdev(values):
    pass

def most_common(values):
    return max(set(values), key=values.count)

def least_common(values):
    return min(set(values), key=values.count)
