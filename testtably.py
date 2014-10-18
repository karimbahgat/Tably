import tably

#data = tably.load(r"D:\My Files\GIS Data\(Easy Georeferencer)\TestingGrounds\(I.np.uts)\GTDinput.txt")
data = tably.load(data=["f1 f2 f3 f4".split(),
                        [1,"h","e",True],
                        [2,"h","e",False],
                        [3,"h","e",True]])

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
#print data

# FIX HOW COPY SELF
#d2 = data.copy()
#print data.join("a2_country", d2, "a2_country")
