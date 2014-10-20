"""
...
"""

import datetime
import itertools


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
    def __str__(self):
        return "<MissingValue>"

MISSING = MissingValue()




def isint(x):
    try:
        conv = float(x)
        return conv.is_integer()
    except ValueError:
        if x == "" or x.isspace(): return True
        return False

def isfloat(x):
    try:
        float(x)
        return True
    except ValueError:
        if x == "" or x.isspace(): return True
        return False

COLUMNTYPES_TEST = dict([("datetime", lambda x: isinstance(x,datetime.datetime) ),
                    ("integer", isint),
                    ("float", isfloat),
                    ("boolean", lambda x: isinstance(x,bool) or x in ("True","False")),
                    ("text", lambda x: True),
                    ("flexi", lambda x: True)])

def forceint(x):
    try:
        return int(x)
    except ValueError:
        if x == "" or x.isspace(): return MISSING

def forcefloat(x):
    try:
        return float(x)
    except ValueError:
        if x == "" or x.isspace(): return MISSING

COLUMNTYPES_FORCE = dict([("datetime", datetime.datetime),
                    ("integer", forceint),
                    ("float", forcefloat),
                    ("boolean", bool),
                    ("text", str),
                    ("flexi", lambda x: x)])


class Column:
    def __init__(self, name, values, label="", dtype=None, value_labels=dict()):
        self.name = name
        self.label = label
        self.values = values
        self.value_labels = value_labels
        if not dtype:
            dtype = self.detect_type()
            self.convert_type(dtype)
        self.type = dtype
        self.columnmapper = None

    def __str__(self):
        uniqvalues = list(str(value)[:50] for value in sorted(set(self)))
        if len(uniqvalues) > 30:
            uniqvalues = uniqvalues[:30]
            uniqvalues.append("...")
        return "Field '%s':"%self.name + \
               "\n  Description: '%s'"%self.label + \
               "\n  Data type: %s"%self.type + \
               "\n  Unique values:" + \
               "\n    " + "\n    ".join(uniqvalues) + \
               "\n"

    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]
            
    def __len__(self):
        return len(self.values)
            
    def __getitem__(self, i):
        # only way is to get values from index(es)
        value = self.values[i]
        value_label = self.value_labels.get(value)
        if value_label: value = value_label
        return value

    def __setitem__(self, i, value):
        # here is the gateway that ensures all values correspond to columntype
        convertfunc = COLUMNTYPES_FORCE[self.type]
        self.values[i] = convertfunc(value)

    def __add__(self, other):
        newcol = self.copy()
        if isinstance(other, Column):
            for i,(val,otherval) in enumerate(itertools.izip_longest(self.values, other.values)):
                if val == MISSING: val = otherval
                if otherval == MISSING: continue
                newcol.values[i] = val + otherval
        else:
            for i,val in enumerate(self.values):
                if val == MISSING: continue
                newcol.values[i] = val + other
        return newcol

    def __radd__(self, other): # in case using sum() which starts with value 0
        newcol = self.copy()
        if isinstance(other, Column):
            for i,(val,otherval) in enumerate(itertools.izip_longest(self.values, other.values)):
                if val == MISSING: val = otherval
                if otherval == MISSING: continue
                newcol.values[i] = otherval + val
        else:
            for i,val in enumerate(self.values):
                if val == MISSING: continue
                newcol.values[i] = other + val
        return newcol

    def __sub__(self, other):
        newcol = self.copy()
        if isinstance(other, Column):
            for i,(val,otherval) in enumerate(itertools.izip_longest(self.values, other.values)):
                if val == MISSING: val = otherval
                if otherval == MISSING: continue
                newcol.values[i] = val - otherval
        else:
            for i,val in enumerate(self.values):
                if val == MISSING: continue
                newcol.values[i] = val - other
        return newcol
                
    def __mul__(self, other):
        newcol = self.copy()
        if isinstance(other, Column):
            for i,(val,otherval) in enumerate(itertools.izip_longest(self.values, other.values)):
                if val == MISSING: val = otherval
                if otherval == MISSING: continue
                newcol.values[i] = val * otherval
        else:
            for i,val in enumerate(self.values):
                if val == MISSING: continue
                newcol.values[i] = val * other
        return newcol

    def __div__(self, other):
        newcol = self.copy()
        if isinstance(other, Column):
            for i,(val,otherval) in enumerate(itertools.izip_longest(self.values, other.values)):
                if val == MISSING: val = otherval
                if otherval == MISSING: continue
                newcol.values[i] = val / float(otherval)
        else:
            for i,val in enumerate(self.values):
                if val == MISSING: continue
                newcol.values[i] = val / float(other)
        return newcol

    @property
    def prev(self):
        if self.columnmapper:
            curindex = self.columnmapper.columns.index(self)
            if curindex > 0:
                return self.columnmapper.columns[curindex-1]
    @property
    def next(self):
        if self.columnmapper:
            curindex = self.columnmapper.columns.index(self)
            if curindex < len(self.columnmapper.columns)-1:
                return self.columnmapper.columns[curindex+1]

    def copy(self):
        newcol = Column(name=self.name,
                        label=self.label,
                        dtype=self.type,
                        values=list(self.values),
                        value_labels=self.value_labels.copy()
                        )
        return newcol

    def detect_type(self):
        # detect the type from looking at the values
        detecttypes = (_dtype for _dtype in "boolean datetime integer float text".split() )
        detecttype = next(detecttypes)
        for value in self:
            if value == MISSING:
                continue
            # check that value is appropriate for that type
            while True:
                if COLUMNTYPES_TEST[detecttype](value):
                    # value appropriate for that type
                    break
                else:
                    # value not appropriate, so never chec for that type again
                    detecttype = next(detecttypes)
        # the current type that remains is the one
        # that can successfully be used for all values
        return detecttype

    def convert_type(self, dtype):
        # convert all values
        convertfunc = COLUMNTYPES_FORCE[dtype]
        for i,value in enumerate(self.values):
            if value == MISSING:
                continue
            newvalue = convertfunc(value)
            self.values[i] = newvalue
        self.type = dtype

    def make_valuelabels_permanent(self):
        if self.value_labels:
            self.type = self.detect_type(self.value_labels.values())
            self.values = [valuelabel for valuelabel in self]
            self.value_labels = dict()

    def recode(self, oldval, newval):
        pass

    def recode_range(self, minval, maxval, newval):
        pass

    def edit(self, **kwargs):
        pass

    def drop(self):
        if self.columnmapper:
            self.columnmapper.columns.remove(self)

class ColumnMapper:
    def __init__(self, columns):
        """
        Takes a list of predefined column instances.
        """
        for col in columns:
            col.columnmapper = self
        self.columns = columns

    def __str__(self):
        fieldtuples = [ "%s (%s)"%(field.name,field.type) for field in self.columns ]
        return "Fields:" + \
               "\n  " + "\n  ".join(fieldtuples) + \
               "\n"

    def __iter__(self):
        for col in self.columns:
            yield col
            
    def __len__(self):
        return len(self.columns)

    def __getitem__(self, i):
        # get either one or more column instances
        # based on either column positions or names
        if isinstance(i, slice):
            start, stop, step = i.start, i.stop, i.step
            start_isfield = isinstance(start, (str,unicode))
            stop_isfield = isinstance(stop, (str,unicode))
            
            if start_isfield or stop_isfield:
                if start_isfield:
                    for column in self.columns:
                        if column.name == start:
                            start = self.columns.index(column)
                            break
                        
                if stop_isfield:
                    for column in self.columns:
                        if column.name == stop:
                            stop = self.columns.index(column) + 1
                            break

                if start > stop: start,stop = stop,start

            columns = self.columns[start:stop:step]
            return ColumnMapper(columns)

        else:
            if isinstance(i, (str,unicode)):
                for column in self.columns:
                    if column.name == i:
                        i = self.columns.index(column)
                        break
                col = self.columns[i]

            elif isinstance(i, (int,float)):
                col = self.columns[i]

            return col

    def __setitem__(self, i, item):
        if isinstance(i, slice): raise Exception("You can only set one field at a time")
        col = self[i]
        colindex = self.columns.index(col)
        if isinstance(item, Column):
            self.columns[colindex] = item
        else:
            for valindex in xrange(len(col)):
                col[valindex] = item

class Row:
    def __init__(self, columnmapper, i):
        self.columnmapper = columnmapper
        self.i = i

    def __str__(self):
        # MAYBE USE PRETTYTABLE FOR FORMATTING: https://code.google.com/p/prettytable/
        rowtuples = []
        for field,value in zip(self.columnmapper.columns, self):
            value = str(value)
            shortvalue = value[:50]
            if len(value) > 50:
                shortvalue[-1] = "..."
            rowtuples.append((field.name,value))
        return "Row #%s:"%self.i + \
               "\n  " + "\n  ".join(("%s: %s"%rowtuple for rowtuple in rowtuples)) + \
               "\n"

    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]
            
    def __len__(self):
        return len(self.columnmapper)
    
    def __getitem__(self, i):
        # get one or more rowvalues, based on either columnfields or column indexes
        if isinstance(i, slice):
            columns = self.columnmapper[i]
            rowvalues = [col[self.i] for col in columns]
        else:
            col = self.columnmapper[i]
            rowvalues = col[self.i]
        return rowvalues

    def __setitem__(self, i, item):
        if isinstance(i, slice): raise Exception("You can only set one rowvalue at a time")
        col = self.columnmapper[i]
        col[self.i] = item

    @property
    def prev(self):
        if self.i > 0:
            return Row(self.columnmapper, self.i - 1)
    
    @property
    def next(self):
        if self.i < len(self.columnmapper.columns[0]) - 1:
            return Row(self.columnmapper, self.i + 1)

    def edit(self, **kwargs):
        pass

    def drop(self):
        for col in self.columnmapper.columns:
            col.values.pop(self.i)

class RowMapper:
    def __init__(self, columnmapper):
        self.columnmapper = columnmapper

    def __str__(self):
        samplerows = []
        looplen = len(self)
        if looplen > 30: looplen = 30
        for i in xrange(looplen):
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
                shortrow_shortvalues[-1] = "."*10
            samplerows.append(shortrow_shortvalues)
        if len(self) > 30:
            samplerows[-1] = ["."*10 for _ in xrange(5)]
        return "Rows:" + \
               "\n  " + "\n  ".join(("[ %s ]" %" , ".join(row) for row in samplerows)) + \
               "\n"

    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]
            
    def __len__(self):
        firstcolumn = self.columnmapper[0]
        return len(firstcolumn)

    def __getitem__(self, i):
        # get one or more row instances
        if isinstance(i, slice):
            start, stop, step = i.start, i.stop, i.step
            rows = [Row(self.columnmapper, _i) for _i in xrange(start,stop,step)]
            columns = []
            for col in self.columnmapper:
                col.values = [col.values[row.i] for row in rows]
                columns.append(col)
            columnmapper = ColumnMapper(columns)
            return RowMapper(columnmapper)
        else:
            return Row(self.columnmapper, i)

    def __setitem__(self, i, item):
        if isinstance(i, slice): raise Exception("You can only set one row at a time")
        if isinstance(item, dict):
            for key,value in item.keys():
                self.columnmapper[key][i] = value
        elif isinstance(item, (list,tuple,Row)):
            for valindex,value in enumerate(item):
                self.columnmapper[valindex][i] = value
        else:
            raise Exception("A row can only be set to a dictionary, iterable, or another row instance")


    





# FUNCTIONS

def build_table(table, fieldtuples, rows, name=None):

    values_bycolumn = itertools.izip_longest(*rows)
    columns = []
    for i,(fieldtuple,values) in enumerate(itertools.izip_longest(fieldtuples,values_bycolumn)):
        values = list(values)
        fieldname,label,dtype,value_labels = fieldtuple
        col = Column(fieldname,values,label,dtype,value_labels)
        columns.append(col)
        
    columnmapper = ColumnMapper(columns)
    rowmapper = RowMapper(columnmapper)

    table.fields = columnmapper
    table.rows = rowmapper

    if not name: name = next(NAMES)
    table.name = name

    return table

def update_rows(table, rows):
    columns = []
    for col in table.fields:
        col.values = [col.values[row.i] for row in rows]
        columns.append(col)
    columnmapper = ColumnMapper(columns)
    table.rows = RowMapper(columnmapper)

def update_fields(table, fields):
    columns = fields
    table.fields = ColumnMapper(columns)







