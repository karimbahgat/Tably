"""
...
"""

import datetime


# CLASSES

def NameGen():
    suffix = 1
    while True:
        suffix += 1
        name = "untitled" + str(suffix)
        yield name

NAMES = NameGen()

class MissingValue:
    def __init__(self):
        pass

MISSING = MissingValue()

class Row:
    def __init__(self, table, i):
        self._table = table
        self._i = i

    def values(self):
        return tuple(self)

    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]
            
    def __len__(self):
        row = self._table._data[self._i]
        return len(row)

    def __str__(self):
        # MAYBE USE PRETTYTABLE FOR FORMATTING: https://code.google.com/p/prettytable/
        rowtuples = []
        for field,value in zip(self._table.fields, self):
            value = str(value)
            shortvalue = value[:50]
            if len(value) > 50:
                shortvalue[-1] = "..."
            rowtuples.append((field.name,value))
        return "Row #%s:"%self._i + \
               "\n  " + "\n  ".join(("%s: %s"%rowtuple for rowtuple in rowtuples)) + \
               "\n"
  
    def __getitem__(self, item):
        if isinstance(item, slice):
            raise ValueError("Range slicing a Row instance is currently not supported")
        row = self._table._data[self._i]
        if isinstance(item, (str,unicode)):
            item = self._table.fields[item]._i
        value = row[item]
        value_label = self._table.fields[item].value_labels.get(value)
        if value_label: value = value_label
        return value

    def remove(self):
        del self._table._data[self._i]

class Rows:
    def __init__(self, table):
        self._table = table

    def __iter__(self):
        for i in xrange(len(self)):
            yield Row(self._table, i)

    def __len__(self):
        return len(self._table._data)

    def __str__(self):
        samplerows = []
        for i in xrange(len(self)):
            row = self[i]
            if len(row) > 5: shortrow = [row[_i] for _i in xrange(5)]
            else: shortrow = [row[_i] for _i in xrange(len(row))]
            shortrow_shortvalues = []
            for value in shortrow:
                value = str(value)
                shortvalue = value.center(10)
                if len(value) > 10:
                    shortvalue = shortvalue[:7]
                    shortvalue += "..."
                shortrow_shortvalues.append(shortvalue)
            if len(row) > 5:
                shortrow_shortvalues[-1] = ["."*10]
            samplerows.append(shortrow_shortvalues)
        if len(self) > 30:
            samplerows[-1] = ["."*10 for _ in xrange(10)]
        return "Rows:" + \
               "\n  " + "\n  ".join(("[ %s ]" %" , ".join(row) for row in samplerows)) + \
               "\n"

    def __getitem__(self, item):
        if isinstance(item, slice):
            raise ValueError("Range slicing a Rows instance is currently not supported")
        return Row(self._table, item)


COLUMNTYPES_TEST = dict([("datetime", lambda x: isinstance(x,datetime.datetime) ),
                    ("integer", lambda x: isinstance(x,int)),
                    ("float", lambda x: isinstance(x,(int,float))),
                    ("boolean", lambda x: isinstance(x,bool)),
                    ("text", lambda x: True)])
    
COLUMNTYPES_FORCE = dict([("datetime", datetime.datetime),
                    ("integer", int),
                    ("float", float),
                    ("boolean", bool),
                    ("text", str)])

class Column:
    def __init__(self, table, i, name, label="", dtype=None, value_labels=dict()):
        self._table = table
        self._i = i

        self.name = name
        self.label = label
        self.value_labels = value_labels

        # if columntype was not given, detect the type from looking at the values
        if not dtype:
            castfuncs = (_dtype for _dtype in "boolean datetime integer float text".split() )
            castfunc = next(castfuncs)
            for value in self:
                if value == MISSING:
                    continue
                # try converting each value
                while True:
                    if COLUMNTYPES_TEST[castfunc](value):
                        # value appropriate for that type of castfunc
                        break
                    else:
                        # value not appropriate, so never chec for that type again
                        castfunc = next(castfuncs)
            # the current cast function that remains is the one
            # that can successfully convert all values
            dtype = castfunc

        # convert all values
        self.type = dtype
        castfunc = COLUMNTYPES_FORCE[dtype]
        for row in self._table._data:
            value = row[self._i]
            if value == MISSING:
                continue
            newvalue = castfunc(value)
            row[self._i] = newvalue
            
    def values(self):
        return tuple(self)

    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]

    def __len__(self):
        return len(self._table.rows)

    def __str__(self):
        uniqvalues = list(sorted(set(str(value)[:50] for value in self)))
        if len(uniqvalues) > 30:
            uniqvalues = uniqvalues[:30]
            uniqvalues.append("...")
        return "Field '%s':"%self.name + \
               "\n  Description: '%s'"%self.label + \
               "\n  Data type: %s"%self.type + \
               "\n  Unique values:" + \
               "\n    " + "\n    ".join(uniqvalues) + \
               "\n"
 
    def __getitem__(self, item):
        if isinstance(item, slice):
            raise ValueError("Range slicing a Column instance is currently not supported")
        row = self._table._data[item]
        value = row[self._i]
        value_label = self.value_labels.get(value)
        if value_label: value = value_label
        return value

    def remove(self):
        for row in self._table._data:
            del row[self._i]
        del self._table.fields._columns[self._i]

class Columns:
    def __init__(self, table):
        self._table = table
        self._columns = []
        # when first created, open-ended column objs are applied to each column
        for i in xrange(len(self._table._data[0])):
            name = "Field%s"%i
            self._columns.append( Column(self._table, i, name) )

    def replace_column(self, i, name, label="", dtype=None, value_labels=dict()):
        column_obj = Column(self._table, i, name, label, dtype, value_labels)
        self._columns[i] = column_obj

    def __iter__(self):
        for column in self._columns:
            yield column

    def __len__(self):
        return len(self._columns)

    def __str__(self):
        fieldtuples = [ "%s (%s)"%(field.name,field.type) for field in self._columns ]
        return "Fields:" + \
               "\n  " + "\n  ".join(fieldtuples) + \
               "\n"

    def __getitem__(self, item):
        if isinstance(item, slice):
            raise ValueError("Range slicing a Columns instance is currently not supported")
        if isinstance(item, (str,unicode)):
            for column in self._columns:
                if column.name == item:
                    return column
            raise KeyError("Fieldname '%s' does not exist"%item)
        else:
            return self._columns[item]









##class Column:
##    def __init__(self, name, values, label="", dtype=None, value_labels=dict()):
##        self.name = name
##        self.label = label
##        self.type = dtype
##        self.values = values
##        self.value_labels = value_labels
##
##    def __iter__(self):
##        for i in xrange(len(self)):
##            yield self[i]
##            
##    def __len__(self):
##        return len(self.values)
##            
##    def __getitem__(self, i):
##        # only way is to get values from index(es)
##        value = self.values[i]
##        value_label = self.value_labels.get(value)
##        if value_label: value = value_label
##        return value
##
##    def detect_type(self):
##        # detect the type from looking at the values
##        detecttypes = (_dtype for _dtype in "boolean datetime integer float text".split() )
##        detecttype = next(detecttypes)
##        for value in self:
##            if value == MISSING:
##                continue
##            # check that value is appropriate for that type
##            while True:
##                if COLUMNTYPES_TEST[detecttype](value):
##                    # value appropriate for that type
##                    break
##                else:
##                    # value not appropriate, so never chec for that type again
##                    detecttype = next(detecttypes)
##        # the current type that remains is the one
##        # that can successfully be used for all values
##        return detecttype
##
##    def convert_type(self, dtype):
##        # convert all values
##        convertfunc = COLUMNTYPES_FORCE[dtype]
##        for i,value in enumerate(self.values):
##            if value == MISSING:
##                continue
##            newvalue = convertfunc(value)
##            self.values[i] = newvalue
##
##    def make_valuelabels_permanent(self):
##        self.values = [valuelabel for valuelabel in self]
##        self.value_labels = dict()
##
##class ColumnMapper:
##    def __init__(self, columns):
##        self.columns = columns
##
##    def __iter__(self):
##        for col in self.columns:
##            yield col
##            
##    def __len__(self):
##        return len(self.columns)
##
##    def __getitem__(self, i):
##        # get either one or more column instances
##        # based on either column positions or names
##        if isinstance(i, slice):
##            start, stop, step = i.start, i.stop, i.step
##            start_isfield = isinstance(start, (str,unicode))
##            stop_isfield = isinstance(stop, (str,unicode))
##            
##            if start_isfield or stop_isfield:
##                if start_isfield:
##                    for column in self.columns:
##                        if column.name == start:
##                            start = self.columns.index(column.name)
##                            break
##                        
##                if stop_isfield:
##                    for column in self.columns:
##                        if column.name == stop:
##                            stop = self.columns.index(column.name)
##                            break
##
##                if start > stop: start,stop = stop,start
##
##            return self.columns[start:stop:step]
##
##        else:
##            if isinstance(i, (str,unicode)):
##                for column in self.columns:
##                    if column.name == i:
##                        i = self.columns.index(column.name)
##                return self.columns[i]
##
##            elif isinstance(i, (int,float)):
##                return self.columns[i]
##
##class Row:
##    def __init__(self, columnmapper, i):
##        self.columnmapper = columnmapper
##        self.i = i
##
##    def __iter__(self):
##        for i in xrange(len(self)):
##            yield self[i]
##            
##    def __len__(self):
##        return len(self.columnmapper)
##    
##    def __getitem__(self, i):
##        # get one or more rowvalues, based on either columnfields or column indexes
##        if isinstance(i, slice):
##            columns = self.columnmapper[i]
##            rowvalues = [col[self.i] for col in columns]
##        else:
##            col = self.columnmapper[i]
##            rowvalues = col[self.i]
##        return rowvalues
##
##class RowMapper:
##    def __init__(self, columnmapper):
##        self.columnmapper = columnmapper
##
##    def __iter__(self):
##        for i in xrange(len(self)):
##            yield self[i]
##            
##    def __len__(self):
##        firstcolumn = self.columnmapper[0]
##        return len(firstcolumn)
##
##    def __getitem__(self, i):
##        # get one or more row instances
##        if isinstance(i, slice):
##            start, stop, step = i.start, i.stop, i.step
##            return [Row(self.columnmapper, _i) for _i in xrange(start,stop,step)]
##        else:
##            return Row(self.columnmapper, i)


    





# FUNCTIONS

def build_table(table, fieldtuples, rows, name=None):
    
    table._data = rows
    table.rows = Rows(table)
    
    _columns = Columns(table)
    for i,fieldtuple in enumerate(fieldtuples):
        fieldname,label,dtype,label_values = fieldtuple
        _columns.replace_column(i, fieldname,label,dtype,label_values)
    table.fields = _columns

    if not name: name = next(NAMES)
    table.name = name

##    table._data = rows
##    table.rows = Rows(table)
##    
##    _columns = Columns(table)
##    for i,fieldtuple in enumerate(fieldtuples):
##        fieldname,label,dtype,label_values = fieldtuple
##        _columns.replace_column(i, fieldname,label,dtype,label_values)
##    table.fields = _columns
##
##    if not name: name = next(NAMES)
##    table.name = name
##
##    return table



