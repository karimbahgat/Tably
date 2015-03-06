from . import class_intervals


def classify(algorithm, values, classes=5):
  """
  Groups a list of values into n non-overlapping classes based on algorithm.

  Available algoritms are:
    - historgram (alias for equal)
    - equal
    - quantile
    - rpretty
    - pretty
    - stdev
    - jenks_sample
    - jenks
  """
  func = class_intervals.__dict__[algorithm]
  breaks = func(values, classes)
  # begin
  values = sorted(values)
  groups = []
  group = []
  prevbreak = breaks.pop(0)
  nextbreak = breaks[0]
  for val in values:
      if val <= nextbreak:
          group.append(val)
      else:
          groups.append(("%s - %s"%(prevbreak,nextbreak), group))
          if len(breaks) >= 2: # dont do for last break pair
            group = [val] # count towards next bin
            prevbreak = breaks.pop(0)
            nextbreak = breaks[0]
  # add last group
  groups.append(("%s - %s"%(prevbreak,nextbreak), group))
  return groups



def membership():
  # groups can be overlapping/nonexclusive
  # either based on index position ranges, or test function
  # not yet implemented
  pass




