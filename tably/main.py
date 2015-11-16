import sys, os, itertools, operator
import urllib
import re
import datetime

import random
import math

from __builtin__ import __dict__ as BUILTINS

from . import loader
from . import builder
from . import saver
from . import stats
from . import gui



class Table:
    def __init__(self, filepath=None, xlsheetname=None, data=None, name=None, encoding="utf8"):
        self.encoding = encoding
        if filepath:
            fieldtuples,rows = loader.from_file(filepath, xlsheetname=xlsheetname)
        elif data:
            fieldtuples,rows = loader.from_list(data)
        else:
            fieldtuples,rows = [],[]
            
        self = builder.build_table(self, fieldtuples, rows, name, encoding=encoding)

    def __len__(self):
        return self.height

    def __unicode__(self):
        return "\n".join([ "Table instance: %s" % self.name,
                           "Width: %s" % self.width,
                           "Height: %s" % self.height,
                           self.fields.__unicode__()[:-1],
                           self.rows.__unicode__() ])

    def __str__(self):
        return self.__unicode__().encode(self.encoding)

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

    def save(self, savepath, encoding="utf8", **kwargs):
        saver.to_file(self, savepath, encoding=encoding, **kwargs)

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

    def to_rows(self, seq):
        """Assuming seq is a sequence of field objs"""
        # detect seq type
        if isinstance(seq, builder.ColumnMapper):
            outtable = self.copy(copyrows=False)
            outtable.add_field(name="variable", type="text")
            outtable.add_field(name="value", type="flexi")
            for row in self:
                for field in seq:
                    rowdict = row.dict
                    rowdict["variable"] = field.name
                    rowdict["value"] = field.values[row.i]
                    outtable.add_row(rowdict)
            # delete old fields that were pivoted
            outtable.drop_fields(*[field.name for field in seq])
            builder.update_rows(outtable, outtable.rows)
            return outtable
        elif isinstace(seq, builder.Column):
            # combine each row with each unique sorted values from column
            pass
        elif isinstance(seq, (list,tuple)):
            pass
        elif isinstance(seq, (str,unicode)):
            pass

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

    def add_field(self, column=None, **kwargs):
        if column == None:
            # note: all new fields are created empty
            kwargs["values"] = [builder.MISSING for _ in xrange(len(self))]
            if not kwargs.get("type"): kwargs["type"] = "flexi"
            kwargs["encoding"] = self.encoding
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
        builder.update_fields(self, self.fields.columns)
        return self

    def drop_fields(self, *dropfields):
        self.fields.columns = [field for field in self.fields if field.name not in dropfields]
        builder.update_fields(self, self.fields.columns)
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

    def _prep_select_eval(self, query):
        # get list of field names mentioned in query    
        # TODO: send this part to separate queryparser module to detect varnames
        # ...it can also take an sql expression and convert each node to equivalent python
        # ALSO, MAYBE LOOK FOR SAFETY LOOPHOLES
        # http://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html
        import ast

        # put entire query on one line in case it had triplequotes with multilines
        query = " ".join([qline.strip() for qline in query.splitlines() if qline])

        # replace each fieldname reference with row['fieldname']
        namenodes = (node for node in ast.walk(ast.parse(query, "<string>", "eval"))
                     if isinstance(node, ast.Name))
        for node in sorted(namenodes,
                           key=lambda n: n.col_offset,
                           reverse=True):
            try:
                eval(node.id) # if no error, is builtin name
                
            except NameError: # if name error, must be field name
                replacetext = "row['%s']" % node.id
                replacestart = node.col_offset
                replaceend = replacestart + len(node.id)
                query = query[:replacestart] + replacetext + query[replaceend:]
                    
        # define some builtins that the user can use
        import random, math, datetime
        vardict = dict(random=random, math=math, datetime=datetime)
        
        # loop rows
        # (2x faster to only loop the relevant columns, since avoids field loopup for each row,
        # ...but not worth it, less understandable, and creates another gateway
        # ...to data values/labels that has to be maintained)
        prepped = compile(query, "<string>", "eval")
        return prepped,vardict
    
    def iter_select(self, query):
        """
        Returns rows where query returns True.
        Query can be a function that takes a single row argument
        and returns True or False.
        Or it can be a Python expression where the value of a field
        is referenced as an ordinary Python variable. 
        """
        # Maybe should return rows instead, or at least need another
        # ...function for that

        if hasattr(query, "__call__"):
            # iterate function results
            for row in self:
                result = query(row)
                if result:
                    yield row
                
        elif isinstance(query, (str,unicode)):
            
            prepped,vardict = self._prep_select_eval(query)
            for row in self:
                # make row available in query
                vardict.update(row=row)
                # run and retrieve query value
                result = eval(prepped, {}, vardict)
                if result:
                    yield row

        else:
            raise Exception("The 'query' argument must either be a query string or a function")

    def select(self, query):
        outtable = self.copy(copyrows=False)
        for row in self.iter_select(query):
            outtable.add_row(row)
        return outtable

    def exclude(self, query):
        outtable = self.copy(copyrows=False)
        # invert query
        if hasattr(query, "__call__"):
            query = lambda row: not query(row)
        else:
            query = "not (%s)" % query
        # run
        for row in self.iter_select(query):
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

    def iter_group(self, fields=None, func=None, query=None):
        """
        Group in any way, low-level used by other convenience function,
        only returns raw data ie groups of rows. 
        """
        # define grouping function
        if fields:
            fieldindexes = [self.fields.columns.index(self[fieldname]) for fieldname in fields]
            groupfunc = lambda x: operator.itemgetter(*fieldindexes)
        elif func:
            groupfunc = func
        elif query:
            groupfunc = lambda row: eval(query)
        
        # group them
        temprows = sorted(self.rows, key=groupfunc)
        for combi,rows in itertools.groupby(temprows, key=groupfunc):
            yield combi,rows

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
            outtable.add_field(name=fieldname, type=field.type)
        if fieldmapping: 
            for fieldname in aggfields:
                field = self.fields[fieldname]
                outtable.add_field(name=fieldname, type=field.type)
        
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

    def compute(self, fieldname, expression, fieldtype="flexi"):
        # NOTE: queries and expressions currently do not validate
        # that value types are of the same kind, eg querying if a number
        # is bigger than a string, so may lead to weird results or errors.
            
        if not fieldname in (field.name for field in self.fields):
            self.add_field(name=fieldname, type=fieldtype)

        if hasattr(expression, "__call__"):
            for row in self:
                row[fieldname] = expression(row)

        elif isinstance(expression, (str,unicode)):
            prepped,vardict = self._prep_select_eval(expression)
            for row in self:
                # make row available in query
                vardict.update(row=row)
                # run and retrieve query value
                row[fieldname] = eval(prepped, {}, vardict)
        
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

    def _prep_join_eval(self, query):
        # get list of field names mentioned in query    
        # TODO: send this part to separate queryparser module to detect varnames
        # ...it can also take an sql expression and convert each node to equivalent python
        # ALSO, MAYBE LOOK FOR SAFETY LOOPHOLES
        # http://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html
        import ast
        
        # put entire query on one line in case it had triplequotes with multilines
        query = " ".join([qline.strip() for qline in query.splitlines() if qline])

        # replace each table.fieldname reference with row1 or row2['fieldname']
        attrnodes = (node for node in ast.walk(ast.parse(query, "<string>", "eval"))
                     if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) )
        
        for node in sorted(attrnodes,
                           key=lambda n: n.col_offset,
                           reverse=True):

            attrcaller = node.value.id
            
            if attrcaller == "main":
                replacetext = "row1['%s']" % node.attr
            elif attrcaller == "other":
                replacetext = "row2['%s']" % node.attr
            else:
                continue
            
            replacestart = node.col_offset
            replaceend = replacestart + len(attrcaller) + len(".") + len(node.attr)
            query = query[:replacestart] + replacetext + query[replaceend:]
            
        # define some builtins that the user can use
        import random, math, datetime
        vardict = dict(random=random, math=math, datetime=datetime)
        
        # loop rows
        # (2x faster to only loop the relevant columns, since avoids field loopup for each row,
        # ...but not worth it, less understandable, and creates another gateway
        # ...to data values/labels that has to be maintained)
        prepped = compile(query, "<string>", "eval")
        return prepped,vardict

    def join(self, othertable, query, mergematches=False, fieldmapping=tuple(), keepall=True, mainprefix="t1_", otherprefix="t2_", choosefunc=None):
        """
        - mainprefix: Prefix for the variables from the main table, defaults to None.
        - otherprefix: Prefix for the variables from the other table, defaults to None.
        - choosefunc: If there is more than one match, and not wanting to do a fieldmapping aggregation,
            instead use a function for choosing which row to keep. 
        """
        # TODO: Allow query function in addition to just string
        output = self.copy(copyrows=False)
        mainwidth,otherwidth = self.width,othertable.width

        # extend fieldnames
        for field in othertable.fields:
            name = field.name
            output.add_field(name=name, label=field.label, type=field.type, value_labels=field.value_labels)

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
        prepped,vardict = self._prep_join_eval(query)
            
        # loop rows
        for row1 in self:
            for row2 in othertable:
                vardict.update(row1=row1, row2=row2)
                match = eval(prepped, {}, vardict)
                
                if match:
                    output.add_row(row1) # add main
                    output[-1].edit(row2) # join the matched fields
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
            output.aggregate(groupfields=[], fieldmapping=fieldmapping)

        # rename fields if requested
        if mainprefix:
            for f in output.fields[:mainwidth]:
                f.edit(name=mainprefix + f.name)
        if otherprefix:
            for f in output.fields[mainwidth:]:
                f.edit(name=otherprefix + f.name)        

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
        fieldnames1,vardict1,prepped1 = self._prep_eval(starttime_expr)
        if endtime_expr:
            fieldnames2,vardict2,prepped2 = self._prep_eval(endtime_expr)
        
        for row in self:
            # build fieldname-value dict
            rowvalues = [row[field] for field in fieldnames1]
            vardict1.update(zip(fieldnames1, rowvalues))
            # run and retrieve startexpr value
            result = eval(prepped1, {}, vardict1)
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
                # build fieldname-value dict
                rowvalues = [row[field] for field in fieldnames2]
                vardict2.update(zip(fieldnames2, rowvalues))
                # run and retrieve startexpr value
                result = eval(prepped2, {}, vardict2)
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

def load(filepath=None, xlsheetname=None, data=None, name=None, encoding="utf8"):
    return Table(filepath, xlsheetname, data, name, encoding=encoding)

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
        outtable.add_field(name=outfield.name, type="flexi")
    #add the rest of the tables
    for table in mergetables:
        for row in table:
            rowdict = row.dict
            outtable.add_row(rowdict)
    #autodetect and set field types
    for field in outtable.fields:
        field.convert_type(field.detect_type())
    #return merged table
    return outtable




