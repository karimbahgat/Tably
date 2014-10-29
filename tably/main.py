import sys, os, itertools, operator
import datetime

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
        saver.to_file(savepath, **kwargs)

    def view(self):
        rows, fields = self.to_list()
        gui.view(rows, fields)

    def copy(self, copyrows=True):
        new = Table()
        # copy table metadata
        if copyrows:
            columns = [builder.Column(field.name,list(field.values),field.label,field.type,field.value_labels)
                           for field in self.fields]
        else:
            columns = [builder.Column(field.name,[],field.label,field.type,field.value_labels)
                           for field in self.fields]
        new.fields = builder.ColumnMapper(columns)
        new.rows = builder.RowMapper(self.fields)
        new.name = next(builder.NAMES)
        # copy time info
        if self.is_temporal:
            new.starttime_expr = self.starttime_expr
            new.endtime_expr = self.endtime_expr
        return new

    def to_list(self):
        pass

    ###### LAYOUT #######

    def sort_rows(self, sortfields, direction="down"):
        self.rows.sort(sortfields, direction)
        return self

    def sort_fields(self, sortattributes=["name"], direction="right"):
        self.fields.sort(sortattributes, direction)
        return self

    def transpose(self):
        "ie switch axes, ie each unique variable becomes a unique row"
        # ...
        pass

    # MAybe use https://pypi.python.org/pypi/pivottable/0.8

    def to_values(self):
        pass

    def to_columns(self):
        pass

    def to_rows(self):
        pass

##    def reshape(self, rows=None, fields=None):
##        """
##        ...define which fields should be on which axis...
##        """
##        pass
   
##    here are some options:
##        variable names to rows
##        rowids to variable names
##        variable values to rows
##        variable values to fields
##    or more systematic:
##                fields  rowids  values
##        fields    -      dis            
##        rowids  splfld    -           
##        values  splfld            -
    
##    aka reshaping, aka melting into ids and measures (ie the ids decide the unit of analysis, the measures say which fieldnames to put in a "variable" field with a corresponding value in a "values" field), and casting the new fields into rows (ie turning variable names into id variables aka disaggregating) or fields (fields)
##    http://had.co.nz/reshape/introduction.pdf
##    def enrich_units(self):
##        "aka shrink the dataset: each observation is made into one or more variables"
##        # either by ranges or distinct categories
##        # optional to force specified categories for the new variables, or build them naturally from observed values
##        # choose to keep or drop the units used to enrich
##        pass
##
##    def finer_unit_of_analysis(self):
##        "aka expand the dataset: each variable is made into one or more observations"
##        # either by ranges or distinct categories
##        # optional to force specified categories for the new units, or build them naturally from observed values
##        # choose to keep or drop the variables used for each new unit of analysis
##        pass

    ###### EDIT #######

    def add_row(self, row):
        for field in self.fields:
            field.values.append(builder.MISSING)
        self.rows[-1] = row
    
    def edit_row(self, **kwargs):
        self.rows[-1] = row

    def keep_rows(self, *rows):
        # by index
        pass

    def drop_rows(self, *rows):
        # by index
        pass

    ###### FIELDS #######

    def add_field(self, field):
        pass

    def edit_field(self, **kwargs):
        pass

    def move_field(self, field, toindex):
        pass

    def keep_fields(self, *keepfields):
        self.fields.columns = [field for field in self.fields if field.name in keepfields]
        return self

    def drop_fields(self, *dropfields):
        self.fields.columns = [field for field in self.fields if field.name not in dropfields]
        return self

    ###### CLEAN #######

    def convert_field(self, fieldname, dtype):
        self.fields[fieldname].convert(dtype)

    def duplicates(self, duplicatefields):
        """
        ...
        """
        pass

    def unique(self):
        """
        ...
        """
        pass        

    def outliers(self, type="stdev"):
        """
        ...
        """
        # see journalism, either stdev or mad
        pass

    def recode(self, field, oldvalue, newvalue):
        """
        ...
        """
        pass

    def recode_range(self, field, minvalue, maxvalue, newvalue):
        """
        ...
        """
        pass

    ###### SELECT #######

    def iter_select(self, query):
        "return a generator of True False for each row's query result"
        # MAYBE ALSO ADD SUPPORT FOR SENDING A TEST FUNCTION
        for row in self:
            # make fields into vars
            for field in self.fields:
                fieldname = field.name
                value = row[fieldname]
                if isinstance(value, (int,float)):
                    value = unicode(value)
                else:
                    value = '"""'+unicode(value).replace('"',"'")+'"""'
                code = "%s = %s"%(fieldname,value)
                exec(code)
            # run and retrieve query value
            yield eval(query)

    def select(self, query):
        outtable = self.copy(copyrows=False)
        for row,keep in zip(self,self.iter_select(query)):
            if keep:
                outtable.add_row(row)
        return outtable

    def exclude(self, query):
        outtable = Table()
        for row,drop in zip(self,self.iter_select(query)):
            if not drop:
                outtable.add_row(row)
        return outtable

    def find(self, query):
        # maybe rename iter_query to this find, so that find can be iterated and can be used to find second, nth, and last occurance and not just the first one.
        pass

    ###### GROUP #######

    def membership(self, classifytype, manualbreaks=None):
        """
        Aka groups into classes or pools, potentially overlap bw groups. 
        ...classify by autorange or manual breakpoints,
        creating and returning a new table for each class...
        """
        pass

    def split(self, splitfields):
        """
        Sharp/distinct groupings.
        """
        fieldindexes = [self.fields.index(field) for field in splitfields]
        temprows = sorted(self.rows, key=operator.itemgetter(*fieldindexes))
        for combi,rows in itertools.groupby(temprows, key=operator.itemgetter(*fieldindexes) ):
            table = self.copy(copyrows=False)
            table.rows = list(rows)
            table.name = str(combi)
            yield table

    def aggregate(self, groupfields, fieldmapping=[]):
        """
        ...choose to aggregate into a summary value, OR into multiple fields (maybe not into multiple fields, for that use to_fields() afterwards...
        ...maybe make flexible, so aggregation can be on either unique fields, or on an expression or function that groups into membership categories (if so drop membership() method)...
        """
        if fieldmapping: aggfields,aggtypes = zip(*fieldmapping)
        aggfunctions = dict([("count",len),
                             ("sum",sum),
                             ("max",max),
                             ("min",min),
                             ("average",stats.average),
                             ("median",stats.median),
                             ("stdev",stats.stdev),
                             ("most common",stats.most_common),
                             ("least common",stats.least_common) ])
        outtable = self.copy(copyrows=False)
        fieldindexes = [self.fields.index(field) for field in groupfields]
        temprows = sorted(self.rows, key=operator.itemgetter(*fieldindexes))
        for combi,rows in itertools.groupby(temprows, key=operator.itemgetter(*fieldindexes) ):
            if not isinstance(combi, tuple):
                combi = tuple([combi])
            # first the groupby values
            newrow = list(combi)
            # then the aggregation values
            if fieldmapping:
                columns = zip(*rows)
                selectcolumns = [columns[self.fields.index(field)] for field in aggfields]
                for aggtype,values in zip(aggtypes,selectcolumns):
                    aggfunc = aggfunctions[aggtype]
                    aggvalue = aggfunc(values)
                    newrow.append(aggvalue)
            outtable.append(newrow)
        outtable.fields = groupfields
        if fieldmapping: outtable.fields.extend(aggfields)
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



##    def split_values(self, field):
##        """
##        based on the values of a field,
##        calculates:
##            ...either each value category or summary of membership groups...
##        and puts them:
##            ...either into more fields or into additional rowids...
##        """
##        pass
##
##    def split_fieldnames(self, fieldnames, field):
##        """
##        based on the fieldvalue for each field for each row, 
##        calculates:
##            ...that fieldname and fieldvalue...
##        and puts them:
##            ...into additional rowids (the fieldname) with the value still in the original field...
##        potentially:
##            ...deleting the old fields...
##        """
##        pass
##
##    def split_rowids(self, rowids, field):
##        """
##        based on the grouped fieldvalues for each rowid, 
##        calculates:
##            ...the summary for that value...
##        and puts them:
##            ...into more fields...
##        potentially:
##            ...deleting duplicate rowids...
##        """
##        pass
##
##    def split_fieldnames_rowids(self, fieldnames, rowids, field):
##        "combines the two above"
##        pass



    ###### ANALYZE #######

    def percent_change(self, before_column_name, after_column_name, new_column_name):
        """
        A wrapper around :meth:`compute` for quickly computing
        percent change between two columns.

        :param before_column_name: The name of the column containing the
            *before* values. 
        :param after_column_name: The name of the column containing the
            *after* values.
        :param new_column_name: The name of the resulting column.
        :returns: A new :class:`Table`.
        """
        def calc(row):
            return (row[after_column_name] - row[before_column_name]) / row[before_column_name] * 100

        return self.compute(new_column_name, NumberType(), calc) 

    def rank(self, key, new_column_name):
        """
        Creates a new column that is the rank order of the values
        returned by the row function.

        :param key:  
        :param after_column_name: The name of the column containing the
            *after* values.
        :param new_column_name: The name of the resulting column.
        :returns: A new :class:`Table`.
        """
        key_is_row_function = hasattr(key, '__call__')

        def null_handler(k):
            if k is None:
                return NullOrder() 

            return k

        if key_is_row_function:
            values = [key(row) for row in self.rows]
            compute_func = lambda row: rank_column.index(key(row)) + 1
        else:
            values = [row[key] for row in self.rows]
            compute_func = lambda row: rank_column.index(row[key]) + 1

        rank_column = sorted(values, key=null_handler)

        return self.compute(new_column_name, NumberType(), compute_func)

    ###### CONNECT #######

    def join(self, othertable, query):
        """
        ...
        """
        pass

    def relate(self, othertable, query):
        """maybe add a .relates attribute dict to each row,
        with each relate dict entry being the unique tablename of the other table,
        containing another dictionary with a "query" entry for that relate,
        and a "links" entry with a list of rows pointing to the matching rows in the other table.
        """
        pass

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

def merge(*mergetables):
    #make empty table
    firsttable = mergetables[0]
    outtable = Table()
    #combine fields from all tables
    outfields = list(firsttable.fields)
    for table in mergetables[1:]:
        for field in table.fields:
            if field not in outfields:
                outfields.append(field)
    outtable.setfields(outfields)
    #add the rest of the tables
    for table in mergetables:
        for rowindex in xrange(table.len):
            row = []
            for field in outtable.fields:
                if field in table.fields:
                    row.append( table[rowindex][field] )
                else:
                    row.append( MISSING )
            outtable.addrow(row)
    #return merged table
    return outtable




