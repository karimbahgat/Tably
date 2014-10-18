# All this means:
#  Field objects get an edit method for functional-style changing multiple properties at once
#  Row objects get an edit method for functional-style changing multiple fieldvalues at once
#  Make a table-level wrapper in functional-style for .edit_field() and .edit_row()
#  Field and Row objects get a .next and .prev property for object oriented looping
#  Field and Row objects get a .drop() method for object-oriented way of deleting themselves
#  As with fields, make a .drop_rows() and .keep_rows() method.
#  Maybe just maybe allow creating new fields from using math operators on field objects directly
#    For instance: table["Average"] = sum(table["1998":"2005"]) / len(table["1998":"2005"])
#    Or: table["RelativeIncome"] = table["Income"]) / max(table["Income"])
# Also give fields .recode() and .recode_range() methods, with wrappers at the table-level





import tably

somedata = tably.load("myfile.dta")



# inspect

print somedata

print somedata.fields

print somedata.rows

print somedata.summary()





# example import from multilevel fields

# give correct field names and labels
field_labels = somedata[0]
for field in somedata.fields:
    
    # set "v" fieldnames to previous + number, with a label from the weird label row
    if field.name.startswith("v"):
        field.name = field.prev.name + "_1" # ? somehow increment
        field.label = field_labels[field.name]
        
    # assign label to normal fieldnames
    else: field.label = field_labels[field.name]
        
# drop weird field labels row
somedata[0].drop()





# clean unnecessaries
for field in somedata.fields:
    if field.name.startswith("Answered at"):
        field.drop()

# specifics
somedata.drop_fields("device","phonenr")
somedata.duplicates(...)






# change layout and types

somedata.sort_rows()
somedata.sort_fields()
somedata.move_field("Date", 0)
somedata.move_field("Country", 1)
somedata.move_field("Province", 2)
somedata.convert_field("Date", "datetime")
somedata.convert_field("Country", "geometry")
somedata.convert_field("Province", "geometry")






# make new fields

#add field, then simple functions
somedata.add_field(name = "Migr_Last3",
                   label = "Migration for last 3 years",
                   value_labels = dict(-99=tably.MISSING) )
somedata.compute("Migr_Last3",
                 "Migr14 + Migr13 + Migr12")

#OR simple function, then editing field afterwards instead
somedata.compute("Migr_Last3",
                 "Migr14 + Migr13 + Migr12")
somedata.edit_field("Migr_Last3",
                    name = "Migr_Last3_edited"
                   label = "Migration for last 3 years",
                   value_labels = dict(-99=tably.MISSING) )

#more advanced functions, row-level
somedata.add_field(name = "MigrAllyrs",
                   label = "Total migration for all years",
                   dtype = "integer" )
for row in somedata:
    row["MigrAllyrs"] = row["Migr89":"Migr14"]

#OR table-level
somedata["MigrAllyrs"] = sum(somedata["Migr89":"Migr14"])
somedata.edit_field("MigrAllyrs",
                   label = "Total migration for all years",
                   dtype = "integer" )





# label some values

#opt1: object oriented
confltypes = somedata["CnflType"]
confltypes.name = "ConflictType"
confltypes.value_labels = dict(1="antigov",2="antigov",3="progov",4="progov")
#OR
confltypes.edit(name="ConflictType",
                valuelabels=dict(1="antigov",2="antigov",3="progov",4="progov"))

#opt2: functional oriented  
somedata.edit_field("CnflType",
                    name="ConflictType",
                    value_labels=dict(1="antigov",
                                      2="antigov",
                                      3="progov",
                                      4="progov"))






# recode some values
somedata.recode_range("Casualties",
                      low=1,
                      high=100,
                      new=1)
somedata.recode_range("Casualties",
                      low=100,
                      high=1000,
                      new=2)
somedata.recode_range("Casualties",
                      low=1000,
                      high=100000,
                      new=3)
somedata.edit_field("Casualties",
                    label="Recoded into low-med-hi categories"
                    value_labels=dict(1:"low",
                                      2:"medium",
                                      3:"high"))





# make all text fields end in "_other"

for field in somedata.fields:
    if field.type == "text" and field.name.endswith("_1"):
        field.name = field.name + "_other"





# looping rows

for row in somedata:
    # do something
    pass

#OR next() style
row = somedata[0]
while True:
    # do something
    row = row.next







# editing some row
for row in somedata:
    row.edit(Author="Karim", Date=date.today(), Time=time.now())








# fun stuff, aggregate!

somedata = somedata.aggregate(...) # for any type of grouping function (uniqrowids, valueranges, or flexible membership), aggregate each group into exactly one row
somedata = somedata.split(...) # for any type of grouping function (uniqrowids, valueranges, or flexible membership), make each group into a new table






# fun stuff, reshape!
## takes any iterable, and uses each elements value for the to_x target value
somedata = somedata.to_rows(somedata.fields["1945":"2014"]) # send a range of year fields to a series of rows (repeated for each row) # automatically uses fieldname when it detects a column instance
somedata = somedata.to_rows(somedata.fields["EventType"]) # send all possible event values to a series of rows (repeated for each row)

somedata = somedata.to_fields(rows)
somedata = somedata.to_fields(values)

somedata = somedata.to_values(fields)
somedata = somedata.to_values(rows)





