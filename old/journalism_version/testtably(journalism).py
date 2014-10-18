import tably

data = tably.load("/Users/karim/Desktop/pyGDELT/data/GDELT_working_EXCEL_wrapper.xlsx")

# print all fields/columns
#print data.fields

# print one column
print data.fields["ac_goldsteinscale"]

# print rows
#for row in data: print row

# print entire table info
print data

# FIX HOW COPY SELF
#d2 = data.copy()
#print data.join("a2_country", d2, "a2_country")
