import sys, os, itertools, operator
import urllib
import re
import datetime

from __builtin__ import __dict__ as BUILTINS

from . import loader
from . import builder
from . import saver
from . import stats
from . import gui



class Table:
    def __init__(self, filepath=None, xlsheetname=None, data=None, name=None):
        if filepath:
            fieldtuples,rows = loader.from_file(filepath, xlsheetname=xlsheetname)
        elif data:
            fieldtuples,rows = loader.from_list(data)
        else:
            fieldtuples,rows = [],[]
            
        self = builder.build_table(self, fieldtuples, rows, name)

    def __len__(self):
        return self.height

    def __str__(self):
        return "\n".join([ "Table instance: %s" % self.name,
                           "Width: %s" % self.width,
                           "Height: %s" % self.height,
                           str(self.fields)[:-1],
                           str(self.rows) ])

    def __iter__(self):
        for row in self.rows:
            yield row

    def __getitem__(self, i):
        """
        Get either one or more Columns of data, 
        or get one or more Rows of data.
        """
        if isinstance(i, slice):

            start, stop = i.start, i.stop
            start_isfield = isinstance(start, (str,unicode))
            stop_isfield = isinstance(stop, (str,unicode))
            if start_isfield or stop_isfield:
                return self.fields[i]

            else:
                return self.rows[i]

        else:

            if isinstance(i, (str,unicode)):
                return self.fields[i]

            elif isinstance(i, (int,float)):
                return self.rows[i]

    def __setitem__(self, i, item):
        """
        Set either a Column of data, 
        or set a Row of data.
        """
        if isinstance(i, slice): raise Exception("You can only set one table element at a time")

        if isinstance(i, (str,unicode)):
            self.fields[i] = item

        elif isinstance(i, (int,float)):
            self.rows[i] = item

    @property
    def width(self):
        return len(self.rows[0])

    @property
    def height(self):
        return len(self.rows)

    ###### GENERAL #######

    def save(self, savepath, **kwargs):
        if not kwargs.get("encoding"): kwargs["encoding"] = builder.CODEC
        saver.to_file(self, savepath, **kwargs)

    def view(self):
        rows, fields = self.to_list()
        gui.view(rows, fields)

    def copy(self, copyrows=True):
        new = Table()
        # copy table metadata
        if copyrows:
            columns = [field.copy() for field in self.fields]
        else:
            columns = [field.copy(keepvalues=False) for field in self.fields]
        new.fields = builder.ColumnMapper(columns)
        new.rows = builder.RowMapper(new.fields)
        new.name = next(builder.NAMES)
        # copy time info
        if self.is_temporal:
            new.starttime_expr = self.starttime_expr
            new.endtime_expr = self.endtime_expr
        return new

    def to_list(self):
        fields = [field.name for field in self.fields]
        rows = [row.list for row in self]
        tolist = [fields]
        tolist.extend(rows)
        return tolist

    ###### LAYOUT #######

    def sort_rows(self, sortfields, direction="down"):
        self.rows.sort(sortfields, direction)
        return self

    def sort_fields(self, sortattributes=["name"], direction="right"):
        self.fields.sort(sortattributes, direction)
        return self

##    # Maybe use https://pypi.python.org/pypi/pivottable/0.8
##
##    def transpose(self):
##        "ie switch axes, ie each unique variable becomes a unique row"
##        # ...
##        pass
##
##    def to_values(self, seq):
##        pass
##
##    def to_columns(self, seq):
##        pass
##
##    def to_rows(self, seq):
##        pass

    ###### EDIT #######

    def add_row(self, row=None, **kwargs):
        for field in self.fields:
            field.values.append(builder.MISSING)
        if row:
            self.rows[-1] = row
        elif kwargs:
            for field,value in kwargs.items():
                self.rows[-1][field] = value
    
    def edit_row(self, i, **kwargs):
        self.rows[i].edit(**kwargs)

    ###### FIELDS #######

    def add_field(self, **kwargs):
        # note: all new fields are created empty
        kwargs["values"] = [builder.MISSING for _ in xrange(len(self))] 
        column = builder.Column(**kwargs)
        self.fields.columns.append(column)
        builder.update_fields(self, self.fields.columns)

    def edit_field(self, fieldname, **kwargs):
        if kwargs.get("values") != None: raise Exception("To modify the values of a field, use the compute method, do not edit its 'values' attribute directly")
        self.fields[fieldname].edit(**kwargs)

    def move_field(self, fieldname, toindex):
        field = self.fields[fieldname]
        field.drop()
        self.fields.columns.insert(field, toindex)
        builder.update_fields(self, self.fields.columns)

    def keep_fields(self, *keepfields):
        self.fields.columns = [field for field in self.fields if field.name in keepfields]
        return self

    def drop_fields(self, *dropfields):
        self.fields.columns = [field for field in self.fields if field.name not in dropfields]
        return self

    ###### CLEAN #######

    def convert_field(self, fieldname, type):
        self.fields[fieldname].convert_type(type)

##    def duplicates(self, duplicatefields):
##        """
##        ...
##        """
##        pass
##
##    def unique(self):
##        """
##        ...
##        """
##        pass        
##
##    def outliers(self, type="stdev"):
##        """
##        ...
##        """
##        # see journalism, either stdev or mad
##        pass

    def recode(self, field, oldvalue, newvalue):
        self.fields[field].recode(oldvalue, newvalue)

    def recode_range(self, field, minvalue, maxvalue, newvalue):
        self.fields[field].recode_range(minvalue, maxvalue, newvalue)

    ###### SELECT #######

    def iter_select(self, query):
        "return a generator of True False for each row's query result"

        if hasattr(query, "__call__"):
            # iterate function results
            for row in self:
                result = query(row)
                yield result
                
        elif isinstance(query, (str,unicode)): 
            for row in self:
                # run and retrieve query value
                yield eval(query)

        else:
            raise Exception("The 'query' argument must either be a query string or a function")

    def select(self, query):
        outtable = self.copy(copyrows=False)
        for row,keep in itertools.izip(self,self.iter_select(query)):
            if keep:
                outtable.add_row(row)
        return outtable

    def exclude(self, query):
        outtable = self.copy(copyrows=False)
        for row,drop in itertools.izip(self,self.iter_select(query)):
            if not drop:
                outtable.add_row(row)
        return outtable

##    def find(self, query):
##        # maybe rename iter_query to this find, so that find can be iterated and can be used to find second, nth, and last occurance and not just the first one.
##        pass

    ###### GROUP #######

##    def membership(self, classifytype, manualbreaks=None):
##        """
##        Aka groups into classes or pools, potentially overlap bw groups. 
##        ...classify by autorange or manual breakpoints,
##        creating and returning a new table for each class...
##        """
##        pass

    def split(self, splitfields):
        """
        Sharp/distinct groupings.
        """
        fieldindexes = [self.fields.columns.index(self[fieldname]) for fieldname in splitfields]
        temprows = sorted(self.rows, key=operator.itemgetter(*fieldindexes))
        for combi,rows in itertools.groupby(temprows, key=operator.itemgetter(*fieldindexes) ):
            table = new()
            for field in self.fields:
                table.add_field(name=field.name, type=field.type)
            for row in rows:
                table.add_row(list(row))
            table.name = unicode(combi)
            yield table

    def aggregate(self, groupfields, fieldmapping=[]):
        """
        ...choose to aggregate into a summary value, OR into multiple fields (maybe not into multiple fields, for that use to_fields() afterwards...
        ...maybe make flexible, so aggregation can be on either unique fields, or on an expression or function that groups into membership categories (if so drop membership() method)...
        """
        if fieldmapping: aggfields,aggtypes = zip(*fieldmapping)
        aggfunctions = dict([("count",stats.len_of),
                             ("sum",stats.sum_of),
                             ("max",stats.max_of),
                             ("min",stats.min_of),
                             ("average",stats.average),
                             ("median",stats.median),
                             ("stdev",stats.stdev),
                             ("most common",stats.most_common),
                             ("least common",stats.least_common) ])
        # extend fields # NOT TESTED...
        outtable = new()
        for fieldname in groupfields:
            field = self.fields[fieldname]
            outtable.add_field(fieldname, type=field.type)
        if fieldmapping: 
            for fieldname in aggfields:
                field = self.fields[fieldname]
                outtable.add_field(fieldname, type=field.type)
        
        # aggregate
        fieldindexes = [self.fields.columns.index(self[fieldname]) for fieldname in groupfields]
        temprows = sorted(self.rows, key=operator.itemgetter(*fieldindexes))
        for combi,rows in itertools.groupby(temprows, key=operator.itemgetter(*fieldindexes) ):
            if not isinstance(combi, tuple):
                combi = tuple([combi])
                
            # first the groupby values
            newrow = list(combi)
            
            # then the aggregation values
            if fieldmapping:
                columns = zip(*rows)
                selectcolumns = [columns[self.fields.columns.index(self[field])] for field in aggfields]
                for aggtype,values in zip(aggtypes,selectcolumns):
                    aggfunc = aggfunctions[aggtype]
                    aggvalue = aggfunc(values)
                    newrow.append(aggvalue)
            outtable.add_row(newrow)
            
        return outtable

    ###### CREATE #######

    def compute(self, fieldname, expression, query=None):
        # NOTE: queries and expressions currently do not validate
        # that value types are of the same kind, eg querying if a number
        # is bigger than a string, so may lead to weird results or errors. 
        if not fieldname in self.fields:
            self.addfield(fieldname)
        expression = "result = %s" % expression
        for row in self:
            # make fields into vars
            for field in self.fields:
                value = row[self.fields.index(field)]
                if isinstance(value, (unicode,str)):
                    value = '"""'+str(value).replace('"',"'")+'"""'
                elif isinstance(value, (int,float)):
                    value = str(value)
                code = "%s = %s"%(field,value)
                exec(code)
            # run and retrieve expression value          
            if not query or (eval(query) == True):
                exec(expression)
                row[self.fields.index(fieldname)] = result
        return self

    ###### ANALYZE #######

##    def percent_change(self, before_column_name, after_column_name, new_column_name):
##        """
##        A wrapper around :meth:`compute` for quickly computing
##        percent change between two columns.
##
##        :param before_column_name: The name of the column containing the
##            *before* values. 
##        :param after_column_name: The name of the column containing the
##            *after* values.
##        :param new_column_name: The name of the resulting column.
##        :returns: A new :class:`Table`.
##        """
##        def calc(row):
##            return (row[after_column_name] - row[before_column_name]) / row[before_column_name] * 100
##
##        return self.compute(new_column_name, NumberType(), calc) 
##
##    def rank(self, key, new_column_name):
##        """
##        Creates a new column that is the rank order of the values
##        returned by the row function.
##
##        :param key:  
##        :param after_column_name: The name of the column containing the
##            *after* values.
##        :param new_column_name: The name of the resulting column.
##        :returns: A new :class:`Table`.
##        """
##        key_is_row_function = hasattr(key, '__call__')
##
##        def null_handler(k):
##            if k is None:
##                return NullOrder() 
##
##            return k
##
##        if key_is_row_function:
##            values = [key(row) for row in self.rows]
##            compute_func = lambda row: rank_column.index(key(row)) + 1
##        else:
##            values = [row[key] for row in self.rows]
##            compute_func = lambda row: rank_column.index(row[key]) + 1
##
##        rank_column = sorted(values, key=null_handler)
##
##        return self.compute(new_column_name, NumberType(), compute_func)

    ###### CONNECT #######

    def join(self, othertable, query, mergematches=False, fieldmapping=tuple(), keepall=True):

        output = self.copy(copyrows=False)

        # extend fieldnames
        for field in othertable.fields:
            if field.name not in (f.name for f in output.fields):
                output.add_field(name=field.name, label=field.label, type=field.type, value_labels=field.value_labels)

##        # extend fieldnames
##        for field in othertable.fields:
##            name = field.name
##            # uniqify name if duplicate
##            count = 1
##            while name in (f.name for f in self.fields):
##                name = field.name + "_%i" %count
##                count += 1
##            output.add_field(name=name, label=field.label, type=field.type, value_labels=field.value_labels)

        # prep twotable query string
        preppedlist = []
        queryitems = query.split()
        for item in queryitems:
            item = item.strip()
            # treat any non-builtin names as a "table.fieldname" string
            try: eval(item)
            except SyntaxError: pass
            except NameError:
                if len(item.split(".")) != 2:
                    raise Exception("fieldnames must be specified as either 'main' or 'other' followed by '.' and the fieldname")
                table,field = item.split(".")
                if table == "main":
                    item = "row1['%s']" %field
                elif table == "other":
                    item = "row2['%s']" %field
            preppedlist.append( item )
        query = " ".join(preppedlist)
            
        # loop rows
        for row1 in self:
            for row2 in othertable:
                match = eval(query)
                
                if match:
                    output.add_row(row1)
                    output[-1].edit(row2)
                    if mergematches:
                        # many-to-one
                        pass
                    else:
                        # one-to-one
                        break
                    
            if not match and keepall:
                # failed to match, but keep anyway
                output.add_row(row1)

        # aggregate based on fieldmapping
        if mergematches:
            # HOW TO AGGREGATE?
            self.aggregate(groupfields=[], fieldmapping=fieldmapping)

        # change self in-place
        self = output
        return self

##    def relate(self, othertable, query):
##        """maybe add a .relates attribute dict to each row,
##        with each relate dict entry being the unique tablename of the other table,
##        containing another dictionary with a "query" entry for that relate,
##        and a "links" entry with a list of rows pointing to the matching rows in the other table.
##        """
##        pass

    ###### TIME #######

    def make_temporal(self, starttime_expr, endtime_expr=None):
        """This adds time awareness to the table's rows, by assigning
        a expr that results in a datetime object from a date field,
        or that builds a dictionary with at least a year entry"""
        self.starttime_expr = starttime_expr
        self.endtime_expr = endtime_expr
        # crunch the numbers
        startexpr = "result = %s" % self.starttime_expr
        if self.endtime_expr: endexpr = "result = %s" % self.endtime_expr
        for row in self:
            # make fields into vars
            for field in self.fields:
                value = row[self.fields.index(field)]
                if isinstance(value, (unicode,str)):
                    value = '"""'+str(value).replace('"',"'")+'"""'
                elif isinstance(value, (int,float)):
                    value = str(value)
                elif isinstance(value, (datetime.datetime)):
                    value = str(value)
                code = "%s = %s"%(field,value)
                exec(code)
            # run and retrieve startexpr value
            exec(startexpr)
            if isinstance(result, datetime.datetime): pass
            elif isinstance(result, dict):
                if result.get("year") == None: raise Exception("the dictionary time needs at least a year entry")
                if result.get("month") == None: result["month"] = 1
                if result.get("day") == None: result["day"] = 1
                result = dict([(key,int(val)) for key,val in result.items()])
                result = datetime.datetime(**result)
            row.time = result
            # run and retrieve endexpr value
            if self.endtime_expr:
                exec(endexpr)
                if isinstance(result, datetime.datetime): pass
                elif isinstance(result, dict):
                    if result.get("year") == None: raise Exception("the dictionary time needs at least a year entry")
                    if result.get("month") == None: result["month"] = 1
                    if result.get("day") == None: result["day"] = 1
                    result = dict([(key,int(val)) for key,val in result.items()])
                    result = datetime.datetime(**result)
                endtime = result
                row.duration = endtime - row.time

    @property
    def starttime(self):
        timestamps = (row.time for row in self)
        return next(sorted(timestamps))

    @property
    def endtime(self):
        if self.endtime_expr:
            timestamps = (row.time+row.duration for row in self)
            return next(sorted(timestamps, reverse=True))
        else:
            timestamps = (row.time for row in self)
            return next(sorted(timestamps, reverse=True))

    @property
    def is_temporal(self):
        return hasattr(self,"starttime_expr")
    

###########

def new():
    return Table()

def load(filepath=None, xlsheetname=None, data=None, name=None):
    return Table(filepath, xlsheetname, data, name)

def web_load(urlpath, savefolder=None, xlsheetname=None, name=None):
    # save to temp location in current dir
    if savefolder == None:
        tempfile = True
        savefolder = "" 
    else: tempfile = False
    
    # load
    filename = os.path.split(urlpath)[1]
    download(urlpath, savefolder)
    filepath = os.path.join(savefolder, filename)
    data = load(filepath, xlsheetname, name=name)
    
    # remove temp file
    if tempfile: os.remove(filepath)
    return data

def download(url, savefolder="", savename=None):
    "download and load dataset or other content from web url"
    if not savename:
        savename = os.path.split(url)[1]
    savepath = os.path.join(savefolder, savename)
    urllib.urlretrieve(url, savepath)

def merge(*mergetables):
    #make empty table
    firsttable = mergetables[0]
    outtable = Table()
    #combine fields from all tables
    outfields = list(firsttable.fields)
    for table in mergetables[1:]:
        for field in table.fields:
            if field.name not in (outfield.name for outfield in outfields):
                outfields.append(field)
    for outfield in outfields:
        outtable.add_field(name=outfield.name, type=outfield.type)
    #add the rest of the tables
    for table in mergetables:
        for row in table:
            rowdict = row.dict
            outtable.add_row(rowdict)
    #return merged table
    return outtable




