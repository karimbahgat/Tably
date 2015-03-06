"""
...
"""

import datetime
import itertools
import operator


# CLASSES

CODEC = "utf8"




def NameGen():
    suffix = 1
    while True:
        suffix += 1
        name = "untitled" + unicode(suffix)
        yield name

NAMES = NameGen()




class MissingValue:
    def __init__(self):
        pass
    
    def __str__(self):
        return "<None>"

    def __repr__(self):
        return self.__str__()

    def __nonzero__(self):
        return False

    def __len__(self):
        return 0

    def __add__(self, other):
        return other

    def __radd__(self, other): # in case using sum() which starts with value 0
        return other

    def __sub__(self, other):
        return -1*other

    def __rsub__(self, other):
        return other
                
    def __mul__(self, other):
        return self

    def __rmul__(self, other):
        return self

    def __div__(self, other):
        return self

    def __rdiv__(self, other):
        return self

    def __float__(self):
        return self

MISSING = MissingValue()

def detect_missing(value):
    if isinstance(value, (str,unicode)):
        if value == "" or value.isspace():
            return True
        elif value.strip().lower() in ("<none>",".","..","-","--","na","n/a","nan","none","missing"):
            return True
    elif value in (MISSING,False,None,):
        return True



def isint(x):
    try:
        conv = float(x)
        return conv.is_integer()
    except ValueError:
        if detect_missing(x): return True
        return False

def isfloat(x):
    try:
        float(x)
        return True
    except ValueError:
        if detect_missing(x): return True
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
        if detect_missing(x): return MISSING

def forcefloat(x):
    try:
        return float(x)
    except ValueError:
        if detect_missing(x): return MISSING

def forcetext(x):
    if detect_missing(x): 
        # is missing value
        return MISSING
    try:
        return unicode(x, CODEC)
    except (ValueError, TypeError):
        if isinstance(x, unicode):
            # value is already unicode
            return x
        else:
            # cannot be converted with a codec, ie int or float
            return unicode(x)

COLUMNTYPES_FORCE = dict([("datetime", datetime.datetime),
                    ("integer", forceint),
                    ("float", forcefloat),
                    ("boolean", bool),
                    ("text", forcetext),
                    ("flexi", lambda x: x)])


class Column:
    def __init__(self, name, values=[], label="", type=None, value_labels=dict()):
        self.name = forcetext(name)
        self.label = forcetext(label)
        if not isinstance(values, list): raise Exception("values argument must be a list of lists")
        self.values = values
        if not isinstance(value_labels, dict): raise Exception("value_labels argument must be a dictionary")
        self.value_labels = value_labels
        
        if not type:
            type = self.detect_type()
            self.convert_type(type)
        self.type = type
        self.columnmapper = None

    def __str__(self):
        uniqvalues = list(unicode(value)[:50] for value in sorted(set(self)))
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
        if detect_missing(value):
            self.values[i] = value
        else:
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
    def i(self):
        return self.columnmapper.columns.index(self)

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

    def copy(self, keepvalues=True):
        if keepvalues:
            newcol = Column(name=self.name,
                            label=self.label,
                            type=self.type,
                            values=list(self.values),
                            value_labels=self.value_labels.copy()
                            )
        else:
            newcol = Column(name=self.name,
                            label=self.label,
                            type=self.type,
                            values=[],
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

    def convert_type(self, type):
        # convert all values
        convertfunc = COLUMNTYPES_FORCE[type]
        for i,value in enumerate(self.values):
            if value == MISSING:
                continue
            newvalue = convertfunc(value)
            self.values[i] = newvalue
        self.type = type

    def recode(self, oldval, newval):
        for i,value in enumerate(self.values):
            if value == oldval:
                self.values[i] = newval

    def recode_range(self, minval, maxval, newval):
        for i,value in enumerate(self.values):
            if value >= minval and value < maxval:
                self.values[i] = newval

    def recode_as_valuelabels(self):
        if self.value_labels:
            self.values = [valuelabel for valuelabel in self]
            self.type = self.detect_type()
            self.value_labels = dict()

    def edit(self, name=None, values=None, label=None, type=None, value_labels=None):
        if name: self.name = forcetext(name)
        if label: self.label = forcetext(label)
        if values:
            if not isinstance(values, list): raise Exception("values argument must be a list of lists")
            self.values = values
        if value_labels:
            if not isinstance(value_labels, dict): raise Exception("value_labels argument must be a dictionary")
            self.value_labels = value_labels
        if type:
            self.convert_type(type)
            self.type = type

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
                    else: raise Exception("Could not find field name %s" %start)
                        
                if stop_isfield:
                    for column in self.columns:
                        if column.name == stop:
                            stop = self.columns.index(column) + 1
                            break
                    else: raise Exception("Could not find field name %s" %stop)

            if (start != None and stop != None) and start > stop: start,stop = stop,start
            if not step: step = 1
            if stop > len(self): stop = len(self)
            columns = self.columns[start:stop:step]
            return ColumnMapper(columns)

        else:
            if isinstance(i, (str,unicode)):
                for column in self.columns:
                    if column.name == i:
                        i = self.columns.index(column)
                        break
                else: raise Exception("Could not find field name %s" %i)
                col = self.columns[i]

            elif isinstance(i, (int,float)):
                col = self.columns[i]

            return col

    def __setitem__(self, i, item):
        if isinstance(i, slice): raise Exception("You can only set one field at a time")

        if isinstance(i, (str,unicode)):
            # create new field if fieldname doesnt already exist
            fieldnames = (field.name for field in self)
            if i not in fieldnames:
                if len(self.columns) > 0:
                    length = len(self.columns[0])
                else: length = 0
                col = Column(name=i, values=[MISSING for _ in xrange(length)])
                self.columns.append(col)
            
        col = self[i]
        colindex = self.columns.index(col)
        if isinstance(item, Column):
            self.columns[colindex] = item
        else:
            for valindex in xrange(len(col)):
                col[valindex] = item

    def sort(self, sortattributes=["name"], direction="right"):
        if not isinstance(sortattributes, (list,tuple)): sortattributes = [sortattributes]
        if direction == "right": reverse = False
        elif direction == "left": reverse = True
        else: raise Exception("direction must be either 'right' or 'left'")
        self.columns = list(sorted(self.columns, key=operator.attrgetter(*sortattributes), reverse=reverse ))

class Row:
    def __init__(self, columnmapper, i):
        self.columnmapper = columnmapper
        self.i = i

    def __str__(self):
        # MAYBE USE PRETTYTABLE FOR FORMATTING: https://code.google.com/p/prettytable/
        rowtuples = []
        for field,value in zip(self.columnmapper.columns, self):
            value = unicode(value)
            shortvalue = value[:50]
            if len(value) > 50:
                shortvalue = shortvalue[:-3] + "..."
            rowtuples.append((field.name,value))
        return "Row #%s:"%self.i + \
               "\n  " + "\n  ".join(("%r: %r"%rowtuple for rowtuple in rowtuples)) + \
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
    def list(self):
        return list(self)

    @property
    def dict(self):
        fields = (col.name for col in self.columnmapper.columns)
        return dict(zip(fields, self))

    @property
    def prev(self):
        if self.i > 0:
            return Row(self.columnmapper, self.i - 1)
    
    @property
    def next(self):
        if self.i < len(self.columnmapper.columns[0]) - 1:
            return Row(self.columnmapper, self.i + 1)

    def edit(self, rowobj=None, **kwargs):
        if rowobj:
            for rowfield in rowobj.columnmapper.columns:
                self[rowfield.name] = rowfield.values[rowobj.i]
        else:
            for field,value in kwargs.items():
                self[field] = value

    def drop(self):
        for col in self.columnmapper.columns:
            col.values.pop(self.i)

    def copy(self):
        return Row(self.columnmapper, self.i)

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
                value = unicode(value)
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
               "\n  " + "\n  ".join(("[ %r ]" %" , ".join(row) for row in samplerows)) + \
               "\n"

    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]
            
    def __len__(self):
        if len(self.columnmapper) == 0:
            return 0
        else:
            firstcolumn = self.columnmapper[0]
            return len(firstcolumn)

    def __getitem__(self, i):
        # get one or more row instances
        if isinstance(i, slice):
            start, stop, step = i.start, i.stop, i.step
            if not step: step = 1
            if stop > len(self): stop = len(self)
            rows = [Row(self.columnmapper, _i) for _i in xrange(start,stop,step)]
            return rows
        else:
            return Row(self.columnmapper, i)

    def __setitem__(self, i, item):
        if isinstance(i, slice): raise Exception("You can only set one row at a time")
        if isinstance(item, dict):
            for key,value in item.items():
                self.columnmapper[key][i] = value
        elif isinstance(item, (list,tuple,Row)):
            for valindex,value in enumerate(item):
                self.columnmapper[valindex][i] = value
        else:
            raise Exception("A row can only be set to a dictionary, iterable, or another row instance")

    def sort(self, sortfields, direction="down"):
        if not isinstance(sortfields, (list,tuple)): sortfields = [sortfields]
        if direction == "down": reverse = False
        elif direction == "up": reverse = True
        else: raise Exception("direction must be either 'down' or 'up'")
        colnames = [col.name for col in self.columnmapper.columns]
        sortfieldindexes = [colnames.index(field) for field in sortfields]
        results = list(sorted(self, key=operator.itemgetter(*sortfieldindexes), reverse=reverse ))
        for col in self.columnmapper.columns:
            col.values = [col.values[row.i] for row in results]
        return self


class Indicator(Table):           
    def __init__(self):
        """
        Contains one or more versions of the indicator in a common date range,
        where the values are measured in different units

        indicator
            unit1
                obs1
                    date1: value
                    date2: value
                    date3: value
                obs2
                    date1: value
                    date2: value
                    date3: value
                obs3
                    date1: value
                    date2: value
                    date3: value
            unit2
                ...
        """
        Table.__init__(self)

    def get_unit(self):
        pass

class Unit:
    def __init__(self):
        """
        Contains a table of observations, eg countries.
        """
        pass

    def get_obs(self):
        pass

class Observation:
    def __init__(self):
        """
        Contains an observation id, along with a timeseries.
        """
        pass

    def get_timeseries(self):
        pass

class TimeSeries:
    def __init__(self):
        """
        Contains an ordered list of date-value tuples
        """
        pass


    





# FUNCTIONS

def build_table(table, fieldtuples, rows, name=None):

    values_bycolumn = itertools.izip_longest(*rows)
    columns = []
    for i,(fieldtuple,values) in enumerate(itertools.izip_longest(fieldtuples,values_bycolumn)):
        values = list(values)
        fieldname,label,type,value_labels = fieldtuple
        col = Column(fieldname,values,label,type,value_labels)
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
        # does it even do anything?
        col.values = [col.values[row.i] for row in rows]
        columns.append(col)
    columnmapper = ColumnMapper(columns)
    table.rows = RowMapper(columnmapper)

def update_fields(table, fields):
    columns = fields
    table.fields = ColumnMapper(columns)







