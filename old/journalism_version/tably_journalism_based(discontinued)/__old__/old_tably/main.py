import sys, os, itertools, operator
import datetime

from . import loader
from . import saver
from . import stats
from . import gui

def NameGen():
    suffix = 1
    while True:
        suffix += 1
        name = "untitled" + str(suffix)
        yield name

NAMES = NameGen()
MISSING = None

class Table:
    def __init__(self, filepath=None, xlsheetname="Sheet1", data=None, name=None):
        if filepath:
            fields,rows = loader.fromfile(filepath, xlsheetname=xlsheetname)
        elif data:
            fields,rows = loader.fromlists(data)
        else:
            fields, rows = [],[]
        self.fields = fields
        self.rows = rows
        if not name: name = next(NAMES)
        self.name = name

    def __len__(self):
        return self.height

    def __str__(self):
        return "\n".join([ "Table instance: %s" % self.name,
                           "Width: %s" % self.width,
                           "Height: %s" % self.height,
                           "Variables:",
                           "\t"+"\n\t".join(self.fields),
                           "Rows:",
                           "\t"+"\n\t".join( [str(row)[:60]
                                    for row in self.rows[:20]] ) ])

    def __iter__(self):
        for row in self.rows:
            yield row

    @property
    def width(self):
        return len(self.rows[0])

    @property
    def height(self):
        return len(self.rows)

    ###### GENERAL #######

    def save(self, savepath, **kwargs):
        saver.tofile(savepath, **kwargs)

    def view(self):
        gui.view(self)

    def copy(self, copyrows=True):
        new = Table()
        # copy table metadata
        new.fields = [field for field in self.fields]
        new.name = next(NAMES)
        # copy rows with metadata
        if copyrows:
            newrows = []
            for row in self:
                newrow = list(row)
                newrow.__dict__.update( [item for item in row.items() if not item[0].startswith("_")] )
                newrows.append(newrow)
            new.rows = newrows
        # copy time info
        if self.is_temporal:
            new.starttime_expr = self.starttime_expr
            new.endtime_expr = self.endtime_expr
        return new

    ###### GET #######

    def row(self, rowindex):
        return self.rows[rowindex]

    def column(self, fieldname):
        "return a new table with just that one field"
        fieldindex = self.fields.index(fieldname)
        return [row[fieldindex] for row in self]

    ###### EDIT #######

    def append(self, row):
        self.rows.append(row)

    def insert(self, row, index):
        self.rows.insert(row, index)

    def replace(self, row, index):
        self.rows.replace(row, index)

    def delete(self, index):
        del self.rows[index]

    ###### LAYOUT #######

    def sort(self, sortfields, direction="down"):
        if direction == "down": reverse = False
        elif direction == "up": reverse = True
        else: raise Exception("direction must be either 'up' or 'down'")
        sortfieldindexes = [self.fields.index(field) for field in sortfields]
        self.rows = list(sorted(self.rows, key=operator.itemgetter(*sortfieldindexes), reverse=reverse))
        return self

    def transpose(self):
        "ie switch axes, ie each unique variable becomes a unique row"
        # ...
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

    ###### FIELDS #######

    def addfield(self, field):
        self.fields.append(field)
        for row in self.rows:
            row.append(MISSING)

    def insertfield(self, field, index):
        pass

    def movefield(self, field, toindex):
        pass

    def renamefield(self, field, newname):
        pass

    def keepfields(self, fields):
        pass

    def deletefields(self, fields):
        pass

    ###### CLEAN #######

    def duplicates(self, duplicatefields):
        """
        ...
        """
        pass

    def recode(self, field, oldvalue, newvalue):
        """
        ...
        """
        pass

    ###### SELECT #######

    def iter_select(self, query):
        "return a generator of True False for each row's query result"
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
            # run and retrieve query value
            yield eval(query)

    def select(self, query):
        outtable = self.copy(copyrows=False)
        for row,keep in zip(self,self.iter_select(query)):
            if keep:
                outtable.append(row)
        return outtable

    def exclude(self, query):
        outtable = Table()
        for row,drop in zip(self,self.iter_select(query)):
            if not drop:
                outtable.append(row)
        return outtable

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

    def split_values(self, field):
        """
        based on the values of a field,
        calculates:
            ...either each value category or summary of membership groups...
        and puts them:
            ...either into more fields or into additional rowids...
        """
        pass

    def split_fieldnames(self, fieldnames, field):
        """
        based on the fieldvalue for each field for each row, 
        calculates:
            ...that fieldname and fieldvalue...
        and puts them:
            ...into additional rowids (the fieldname) with the value still in the original field...
        potentially:
            ...deleting the old fields...
        """
        pass

    def split_rowids(self, rowids, field):
        """
        based on the grouped fieldvalues for each rowid, 
        calculates:
            ...the summary for that value...
        and puts them:
            ...into more fields...
        potentially:
            ...deleting duplicate rowids...
        """
        pass

    def split_fieldnames_rowids(self, fieldnames, rowids, field):
        "combines the two above"
        pass


    ###### ANALYZE #######

    def aggregate(self, groupfields, fieldmapping=[]):
        """
        ...choose to aggregate into a summary value, OR into multiple fields...
        """
        if fieldmapping: aggfields,aggtypes = zip(*fieldmapping)
        aggfunctions = dict([("count",len),
                             ("sum",sum),
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

    def disaggregate(self, ungroupfields, fieldmapping=[]):
        """
        ...turn one row into multiple rows, each taking their value from specified fields...
        """
        pass

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

def load(filepath=None, xlsheetname="Sheet1", data=None, name=None):
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




