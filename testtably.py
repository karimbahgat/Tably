import tably


#data = tably.load(r"D:\My Files\GIS Data\(Easy Georeferencer)\TestingGrounds\(I.np.uts)\GTDinput.txt")
data = tably.load(data=["f1 f2 f3 f4 f5".split(),
                        [1,3,"h","e",True],
                        [2,4,"h","e",False],
                        [3,5,"h","e",True]])

# print all fields/columns
print ""
print "test all fields"
print data.fields

# print one column
print ""
print "test one field at a time"
print data.fields["f1"]
print data.fields["f2"]
print data.fields["f3"]
print data.fields["f4"]

# print all rows
print ""
print "test all rows"
print data.rows

# print one row
print ""
print "test one row at a time"
for row in data.rows:
    print row

# play with labels
print ""
print "test labeling values"
data.fields["f1"].value_labels = {1:-99}
data.fields["f3"].value_labels = {"e":-88}
data.fields["f2"].value_labels = {"h":"dsf"}
print data.rows

# print entire table info
print data

# math between field instances
print data["f1"] + 4
print data["f2"] * 10
print data["f3"] + data["f4"]
print data["f1":"f2"]
print sum(data["f1":"f2"])/len(data["f1":"f2"]) # note, sum doesnt work on strings

# load heavy tables
import time
t = time.time()
tably.builder.CODEC = "latin"
heavy = tably.load(r"D:\My Files\GIS Data\(Easy Georeferencer)\TestingGrounds\(I.np.uts)\GTDinput.txt")
print time.time() - t, "secs"
print heavy
print heavy["country_txt":"provstate"]
print heavy["country_txt"] + ", " + heavy["provstate"]
for field in heavy["country":"city"]: print field
print heavy["nkill"]

# test sorting
heavy.sort_rows("nkill")
heavy.sort_fields()

# test python builtins treating columns as lists
print heavy[102] # unicode print problem, should be fixed, but only displays raw binary of special chars
for row in heavy[-5:]: 
    print row
for pair in zip(heavy["country_txt"],heavy["nkill"]):
    print pair

# test selection query
print heavy.select("nkill < 0")["nkill"]

    
# FIX HOW COPY SELF
print data

data2 = tably.new()
data2.add_field(name="nr", dtype="integer")
for _ in xrange(5):
    data2.add_row(nr=3)
print data2

joined = data.join(data2, "main.f3 == 'h' and not main.f5", keepall=False)
for lst in joined.to_list():
    print lst



