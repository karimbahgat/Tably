"""
Tablereader
A pure-Python user-friendly reader and analyzer for common dataset formats.
Still not finished completely, and not working on Python 3.x

Copyright 2014 Karim Bahgat
"""

#TODO: FIXUP EVERYTHING ALA SHAPEREADER STYLE

################
# IMPORTS
################
# Import main modules
import imp, csv, os, sys, time, pickle, traceback, difflib, datetime, codecs, operator, math, shutil, urllib, decimal

# Import fileformat modules
import fileformats
import fileformats.shapefile_fork as pyshp
import fileformats.xlrd as xlrd
#import fileformats.savReaderWriter as savReaderWriter
import fileformats.PyDTA as PyDTA

# Import custom modules
import aggregator
from textual import txt, encode
from messages import Report



#PYTHON VERSION CHECKING
import sys
PYTHON3 = int(sys.version[0]) == 3
if PYTHON3:
    basestring = str
    xrange = range
    def listrange(nr):
        return list(range(nr))
    def izip(*inlists):
        return zip(*inlists)
    def listzip(*inlists):
        return list(zip(*inlists))
else:
    import itertools
    def listrange(nr):
        return range(nr)
    def izip(*inlists):
        return itertools.izip(*inlists)
    def listzip(*inlists):
        return zip(*inlists)


################
# MODULE CLASSES
################

#>>>>>>>>>>>>>>>>>
class Table:
    """
    A table instance holding all the information about a loaded table.
    Should not be created directly by the user, only as a result of the 
    LoadFile or CreateEmptyTable functions.

    In addition to the methods described below you may also:
    - Iterate through the table to get each of its rows, eg `for row in MyTable: print row`
    - Measure the number of records with the builtin len() function, eg `print len(MyTable)`
    - And retrieve one or more specific row numbers by using indexing, eg `ninthrecord = MyTable[8]`.
    """
    def __init__(self, tablepath=None, data=None, delimiter="not specified", xlsheetname=None, displaydetails=False):
        if tablepath:
            self._loadfromfile(tablepath, data, delimiter, xlsheetname, displaydetails)
        elif data:
            self._loadfromfile(data=data, displaydetails=displaydetails)
        else:
            self.readerobj = []
            self.filetype = "virtual list table"
            self.joinconditions = dict()
            self.tempoutput = list()
            self.invisiblefields = []
            #do nothing, empty table created, must be loaded later or populated manually row by row
            pass
    def __iter__(self):
        for row in self.readerobj:
            yield row
    def __len__(self):
        return self.len
    def __getitem__(self, fetchindex):
        return self.FetchEntireRow(fetchindex)

    #internal functions only
    def _loadfromfile(self, tablepath=None, data=None, delimiter="not specified", xlsheetname=None, displaydetails=False):
        #define input attributes
        self.tablepath = tablepath
        self.delimiter = delimiter
        if xlsheetname != None:
            self.xlsheetname = xlsheetname
        self.displaydetails = displaydetails
        #determine filetype
        if tablepath:
            if tablepath.endswith(".txt"):
                self.filetype = "txt"
            elif tablepath.endswith(".csv"):
                self.filetype = "csv"
            elif tablepath.endswith((".xls", ".xlsx")):
                self.filetype = "excel"
            elif tablepath.endswith(".dbf"):
                self.filetype = "dbf"
            elif tablepath.endswith(".shp"):
                self.filetype = "shp"
            elif tablepath.endswith(".dta"):
                self.filetype = "dta"
            elif tablepath.endswith(".sav"):
                self.filetype = "spss"
            else:
                raise TypeError("Could not create a table from the given filepath: the filetype extension is either missing or not supported")
        elif data:
            self.filetype = "virtual list table"
        #create readerobject and retrieve fieldnames
        if self.filetype in ("txt","csv"):
            fileobj = open(tablepath, 'rU')
            if self.delimiter == "not specified":
                dialect = csv.Sniffer().sniff(fileobj.read())
                fileobj.seek(0)
                self.readerobj = csv.reader(fileobj, dialect)
            else:
                self.readerobj = csv.reader(fileobj, delimiter=self.delimiter)
            self.fields = [txt(field) for field in next(self.readerobj)]
            self.readerobj = [[txt(eachcell) for eachcell in eachrow] for eachrow in self.readerobj]
        elif self.filetype == "excel":
            workbook = xlrd.open_workbook(tablepath)
            self.excelobj = workbook.sheet_by_name(xlsheetname)
            self.readerobj = [ [txt(self.excelobj.cell_value(row, column)) for column in range(self.excelobj.ncols)] for row in range(1,self.excelobj.nrows)]
            self.fields = [ txt(self.excelobj.cell_value(0, column)) for column in range(self.excelobj.ncols) ]
        elif self.filetype == "dbf" or self.filetype == "shp":
            redirectpathtodbf = "\\".join(tablepath.split(".")[:-1])+".dbf"
            fileobj = open(redirectpathtodbf, 'rb')
            shapereader = pyshp.Reader(dbf=fileobj)
            self.readerobj = [ [txt(eachcell) for eachcell in eachrecord] for eachrecord in shapereader.iterRecords()]
            self.fields = [txt(eachfieldlist[0]) for eachfieldlist in shapereader.fields[1:]]
        elif self.filetype == "spss":
            spssreader = savReaderWriter.SavReader(tablepath)
            spssvalueLabels = spssreader.valueLabels
            datalist = []
            for r, eachrow in enumerate(spssreader):
                labeledrow = []
                for i, eachvalue in enumerate(eachrow):
                    try:
                        label = spssvalueLabels[spssvarNames[i]][eachvalue]
                    except:
                        label = eachvalue
                    labeledrow.append(label)
                datalist.append(labeledrow)
            self.readerobj = readerlist
            self.fields = [eachvar for eachvar in spssreader.varNames]
        elif self.filetype == "dta":
            fileobj = open(tablepath, "rb")
            statareader = PyDTA.StataTools.Reader(fileobj, missing_values=False)
            self.readerobj = [ [txt(eachcell) for eachcell in statareader[rowi] ] for rowi in xrange(len(statareader))]
            self.fields = [txt(eachvar) for eachvar in statareader.variables()]
        elif self.filetype == "virtual list table": #dont convert to txt cus virtual
            self.readerobj = [list(eachrow) for eachrow in data]
            self.fields = self.readerobj.pop(0)
        #other stuff
        self.joinconditions = dict()
        self.tempoutput = list()
        #add unique rowid if file is shapefile
        if self.filetype == "shp":
            self.add_uniqueid("SHAPEID")
        self.invisiblefields = ["SHAPEID"]
        #done
        Report("the table has "+txt(self.height)+" rows")
    
    #define some functions to be used by user
    def _findfieldnameindex(self, fieldname):
        """
        Internal use only.
        """
        return self.fields.index(fieldname)
    def getrow(self, row):
        """
        Returns an entire row as a list

        - row: the index nr of the row to fetch
        """
        return self.readerobj[row]
    def getcolumn(self, column):
        pass
    def getcell(self, row, field):
        """
        Returns the contents of a specific cell.

        - row: the index nr of the row from which to grab the value
        - field: the fieldname of the value to grab
        """
        #determine field index
        if isinstance(field, int) == True:
            column = field
        elif isinstance(field, basestring) == True:
            column = self._findfieldnameindex(field)
        #read and convert to unicode if text, TEMPORARILY DISABLED BC WHOLE TABLE IS LOADED TO UNICODE EITHER WAY
        readvalue = self.readerobj[row][column]
        return readvalue
    @property
    def height(self):
        return len(self.readerobj)
    @property
    def width(self):
        return len(self.readerobj[0])
    def sort(self, sortfields, direction="down"):
        """
        Sorts the table in place. The new sorting will be remembered for future iterations through the table.

        - sortfields: a list of fieldname strings to use for the sorting. Can be one or multiple.
        - direction: a string indicating whether to sort from lowest to highest valuse "down" or "up".
        """
        if not isinstance(sortfields, list):
            Report("error: the sortfields argument in the sort method must be a list")
            return
        #determine sort direction
        if direction == "down":
            reverse = False
        elif direction == "up":
            reverse = True
        else:
            Report("error: direction argument must be either 'down' or 'up'")
        #run sort
        sortfieldindexes = [ self._findfieldnameindex(eachsort) for eachsort in sortfields ]
        self.readerobj = sorted(self.readerobj, key=operator.itemgetter(*sortfieldindexes), reverse=reverse)
    def aslist(self):
        """
        Returns the entire table as a list of lists, only the values themselves, not the fieldnames.
        """
        return self.readerobj
    def save(self, savepath):
        """
        Saves the table based on its current state to a tab-delimited text file.

        - savepath: the filepath of where to save the table, .txt extension included. The only exception is for .shp files which will be saved in the shapefile format.
        """
        Report("saving table")
        if self.filetype == "shp":
            # create writer
            shapewriter = pyshp.Writer()
            shapewriter.autoBalance = 1
            # add fields in correct fieldtype
            for fieldname in self.fields:
                if not fieldname.startswith(tuple(self.invisiblefields)):
                    fieldtype = "C"
                    fieldlen = 250
                    decimals = 6
                    for rowindex in range(self.len):
                        readvalue = self.ReadRow(rowindex, fieldname)
                        if readvalue != "":
                            try:
                                #make nr fieldtype if content is nr
                                float(readvalue)
                                fieldtype = "N"
                                fieldlen = 16
                                decimals = 6
                            except:
                                #but turn to text if any of the cells cannot be made to float bc they are txt
                                fieldtype = "C"
                                fieldlen = 250
                                break
                    # cut out chars in middle if fieldname longer than 10 chars
                    fieldname = str(fieldname[:5])+str(fieldname[-5:])
                    # write field
                    shapewriter.field(encode(fieldname), fieldtype, fieldlen, decimals)
            # sort table based on unique id so as to match with shape positions
            self.sort(sortfields=["SHAPEID"])
            # iterate through original shapes
            shpobj = open(self.tablepath, 'rb')
            shapereader = pyshp.Reader(shp=shpobj)
            shapeindex = 0
            rowindex = 0
            for eachshape in shapereader.iterShapes():
                if shapeindex < self.len:
                    if shapeindex == int(self.ReadRow(rowindex, "SHAPEID")):
                        shapewriter._shapes.append(eachshape)
                        shapewriter.record(*[encode(eachcell, strlen=250, floatlen=16, floatprec=6) for index, eachcell in enumerate(self.FetchEntireRow(rowindex)) if not self.fields[index].startswith(tuple(self.invisiblefields))])
                        rowindex += 1
                    shapeindex += 1
                else:
                    break
            # save
            shapewriter.save(savepath)
            # finally copy prj file from original if exists
            copyfrom = ".".join(self.tablepath.split(".")[:-1])+".prj"
            if os.path.exists(copyfrom):
                copyto = ".".join(savepath.split(".")[:-1])+".prj"
                shutil.copy(copyfrom, copyto)
        else:
            # create output file
            fileobj = open(savepath, "wb")
            writer = csv.writer(fileobj, delimiter="\t")
            # first write fields
            writer.writerow([fieldname for fieldname in self.fields if not fieldname.startswith(tuple(self.invisiblefields))])
            # then write values
            for rowindex in range(self.len):
                eachrow = [encode(eachcell) for index, eachcell in enumerate(self.FetchEntireRow(rowindex)) if not self.fields[index].startswith(tuple(self.invisiblefields))]
                writer.writerow(eachrow)
        # finished
        Report(savepath)
    def add_joincondition(self, mainfield, joinfield, matchpercent=100):
        """
        Adds a set of conditions for performing a tablejoin.
        Multiple join conditions can be specified, making for
        very flexible and powerful joins. Each condition you add
        is remembered until you perform the actual join or reset the
        join conditions. 

        - mainfield: the string name of the field from the original table
        - joinfield: the string name of the field from the external table to be joined to the original table
        - mathpercent: a percent integer nr from 1-100, representing how similar the values in the main and join fields have to be in order join each row (ie the fuzzy join threshold).
        """
        if not isinstance(joinfield, list):
            joinfield = [joinfield]
        if not isinstance(mainfield, list):
            mainfield = [mainfield]
        newjoincondition = dict()
        newjoincondition.update( {"mainfield":mainfield} )
        newjoincondition.update( {"joinfield":joinfield} )
        newjoincondition.update( {"matchpercent":matchpercent} )
        joinconditionID = ";".join([str(eachsetting) for eachsetting in [mainfield,joinfield,matchpercent]])
        self.joinconditions.update( {joinconditionID:newjoincondition} )
    def reset_joinconditions(self):
        """
        Reset/forget about the join conditions set so far.
        """
        self.joinconditions.clear()
    def createjoin(self, jointable, mergematches=False, fieldmapping=(), keepall=True, displaydetails=False):
        """
        This is what performs the actual join between the main and the external table.
        Requires that you have set some join conditions.

        - jointable: a loaded table instance of the external table you wish to join to the main table.
        - *mergematches: a boolean of whether to merge multiple matching rows into a single row (currently not working)
        - *fieldmapping: a set of instructions on how to aggregate the various field values together if merging is set to True (currently not working)
        - *keepall: a boolean of whether to keep all values (default), or only to keep the ones that matched.
        - *displaydetails: a boolean of whether to print detailed information about the join process (default is False).
        """
        ### CAN DETECT AND JOIN IF ANY MATCH FROM A RANGE OF INPUT FIELDS
        ### CURRENTLY ONLY ONE-TO-ONE, CANNOT JOIN MANY TO ONE WITH VALUE AGGREGATING, BUT MAYBE LATER
        ### CODE SHOULD BE SIMPLIFIED...
        ### ALSO, JUNK,SIMILAR,AND BLANK LISTS SHOULD ALSO BE CLEANED

        ### JOIN MERGE ALMOST WORKING, BUT JOIN IN GENERAL IS ONLY MATCHING 1000ish of 8000 cases

        # define stuff
        JunkList = ['*', '?', ' suburban ', ' urban ', ' rural '] # to be removed, must have space on both sides
        JunkList2 = ['-', "'", '.'] # to be replaced by space
        SimilarList = [['mount', 'mt'], ['mont', 'mt'], ['island', 'isl'], ['saint ', 'st '], ['th', 't'], ['ch', 'tj'], ['c', 'k'], ['dh', 'd'], ['kh', 'k'], ['gh', 'g'], ['g', 'j'], ['aa', 'a'], ['i', 'y'], ['z', 's'], [' al ', ' el ']] # first instance is to by replaced by second instance, only two instances per sublist allowed
        blankvalues = ["", " ", "(Missing)", "NONE"]
        def clean_name(placename):
            if matchpercent < 100:
                CLget = " ".join(placename.split())
                CLget = CLget.lower()
                CLgetclean = CLget
                for junk in tuple(JunkList):
                    if CLgetclean.startswith((junk)[1:]):
                        CLgetclean = CLgetclean.replace((junk)[1:], '')
                    if CLgetclean.endswith((junk)[0:len(junk)-1]):
                        CLgetclean = CLgetclean.replace((junk)[0:len(junk)-1], '')
                    if CLgetclean.find(junk):
                        CLgetclean = CLgetclean.replace(junk, '')
                for junk2 in tuple(JunkList2):
                    if CLgetclean.startswith((junk2)[1:]):
                        CLgetclean = CLgetclean.replace((junk2)[1:], '')
                    if CLgetclean.endswith((junk2)[0:len(junk)-1]):
                        CLgetclean = CLgetclean.replace((junk2)[0:len(junk2)-1], '')
                    if CLgetclean.find(junk2):
                        CLgetclean = CLgetclean.replace(junk2, '')
                CLgetstnd = CLgetclean
                for simcomb in tuple(SimilarList):
                    CLgetstnd = CLgetstnd.replace(simcomb[0], simcomb[1])
                return CLgetstnd
            else:
                return placename
        def flattentable(table, fieldfields):
            fieldslist = jointable.fields
            flatvalues_nodupl = set()
            flatvalues = dict()
            flatindexes = dict()
            flatindex = 0
            for index, row in enumerate(table):
                #add all names from all fields and multifields
                for field in fieldfields:
                    #only add if not blank value
                    value = row[fieldslist.index(field)]
                    if value not in blankvalues:
                        flatvalues_nodupl.add(clean_name(value))
                        flatvalues.update( {flatindex:clean_name(value)} )
                        flatindexes.update( {flatindex:index} )
                        flatindex += 1
            flatlookup = dict()
            flatlookup.update( {"values":flatvalues} )
            flatlookup.update( {"values_nodupl":flatvalues_nodupl} )
            flatlookup.update( {"indexes":flatindexes} )
            return flatlookup

        # Flatten jointable multifields to single list while storing index nrs
        Report("flattening tables")
        alljoinlookups = dict()
        for joinconditionID in self.joinconditions:
            # load settings
            joinconditionindex = self.joinconditions.keys().index(joinconditionID)
            joinsettings = self.joinconditions[joinconditionID]
            joinfield = joinsettings["joinfield"]
            matchpercent = joinsettings["matchpercent"]
            if matchpercent == 100:
                #self.invisiblefields.extend(joinfield) IGNORES ORIGINAL MAINJOINFIELD TOO, NEED TO FIND BETTER WAY
                self.invisiblefields.append("MATCHPRC"+str(joinconditionindex+1))
            # collect values
            joinlookup = flattentable(jointable.aslist(), joinfield)
            # write values
            alljoinlookups.update( {joinconditionID:joinlookup} )            
        # Main join stuff
        Report("joining tables")
        def fuzzyjoin():
            # CREATE EMPTY JOIN TABLE
            newtable = []
            # FIELDS
            matchresultfields = ["MATCHPRC"]
            matchresultfields = [ eachfield+str(index+1) for eachfield in matchresultfields for index in range(len(self.joinconditions)) ]
            combinedfields = self.fields
            combinedfields.extend(jointable.fields)
            combinedfields.extend(matchresultfields)
            newtable.append(combinedfields)
            # ROWS
            checkpercentincr = 10
            checkpercent = checkpercentincr
            checkevery = int((self.len/100.0)*checkpercent)
            progressthresh = checkevery
            for rowindex in range(self.len):
                Report("-----", displaydetails)
                if rowindex == progressthresh:
                    print (str(checkpercent)+" percent")
                    progressthresh += checkevery
                    checkpercent += checkpercentincr
                # all joinconditions must be satisfied
                fuzzylist = []
                matchindex = []
                joinconditionindex = 0
                eachmainfieldindex = 0
                while joinconditionindex < len(self.joinconditions):
                    joinconditionsatisfied = False
                    joinconditionID = self.joinconditions.keys()[joinconditionindex]
                    oldmatchindex = matchindex
                    matchindex = []
                    # load joinsettings
                    joinsettings = self.joinconditions[joinconditionID]
                    mainfield = joinsettings["mainfield"]
                    matchpercent = joinsettings["matchpercent"]
                    # load lookupinfo from jointable
                    joinlookup = alljoinlookups[joinconditionID]
                    joinvalues = joinlookup["values"]
                    joinvalues_nodupl = joinlookup["values_nodupl"]
                    joinindexes = joinlookup["indexes"]
                    # begin comparing eachfield, continuing only from last checked field
                    while eachmainfieldindex < len(mainfield):
                        eachmainfield = mainfield[eachmainfieldindex]
                        eachmainfieldvalue = clean_name(self.ReadRow(rowindex, eachmainfield))
                        # start by adding original main rows
                        newrow = self.FetchEntireRow(rowindex)
                        # test if blank row
                        if eachmainfieldvalue in blankvalues:
                            Report([eachmainfieldvalue,"blank"], displaydetails)
                        # then add the rows from the compare table at the end IF there is a MATCH
                        elif eachmainfieldvalue in joinvalues_nodupl:
                            matchindex.extend([ joinindexes[flatindex] for flatindex in joinvalues if eachmainfieldvalue == joinvalues[flatindex] ] )
                        # then try fuzzy match
                        elif matchpercent < 100:
                            try:
                                fuzzymatch = difflib.get_close_matches(eachmainfieldvalue, list(joinvalues_nodupl), 1, float(matchpercent/100.0))[0]
                                newmatchindex = [joinindexes[flatindex] for flatindex in joinvalues if fuzzymatch == joinvalues[flatindex] ]
                                matchindex.extend(newmatchindex)
                                fuzzylist.extend(newmatchindex)
                            except:
                                pass
                        Report([eachmainfieldvalue,matchindex], displaydetails)
                        eachmainfieldindex += 1
                    # test if previous and current joincond true for same row
                    if joinconditionindex > 0:
                        matchindex = list(set(matchindex).intersection(oldmatchindex))
                    # if found matches from first joincondition then evaluate next joincondition starting from first field again
                    if matchindex != []:
                        eachmainfieldindex = 0
                        joinconditionindex += 1
                    # elif no matches, that means joincondition is broken and quit
                    else:
                        break
                # if all conditions satisfied then extend newrow with info from jointable row
                if matchindex != []:
                    Report(["matchindex:",matchindex], displaydetails)
                    newrow.extend(jointable.FetchEntireRow(matchindex[0]))
                    newrow.extend(["" for each in matchresultfields])
                    # add extra matchfields
                    for extrafield in matchresultfields:
                        if matchindex[0] in fuzzylist:
                            if extrafield.startswith("MATCHPRC"):
                                # NOT CORRECT WAY OF WRITING MATCHRATIO, MUST FIX, ONLY DOES MOST RECENT AND ONLY MINIMUM THRESHOLD INSTEAD OF ACTUAL SIMILARITY FOR THAT FIELD, MUST FIX
                                ##self.joinconditions[joinconditionID]
                                writevalue = matchpercent
                            Report(["fuzzy",eachmainfieldvalue], displaydetails)
                            pass
                        else:
                            if extrafield.startswith("MATCHPRC"):
                                writevalue = 100
                            Report(["normal",eachmainfieldvalue], displaydetails)
                            pass
                        newrow[newtable[0].index(extrafield)] = writevalue
                # blank mainfieldvalue or no match found, populate empty blanks for rest of row
                else:
                    Report(["fail",eachmainfieldvalue], displaydetails)
                    newrow.extend(["" for lengthof in range(jointable.width+len(matchresultfields))])
                    for extrafield in matchresultfields:
                        if extrafield.startswith("MATCHPRC"):
                            writevalue = 0
                        newrow[newtable[0].index(extrafield)] = writevalue
                # append whatever changes to newrow and skip to next loop row
                if keepall == True:
                    newtable.append(newrow)
                # if not keepall then only append if found match
                elif matchindex != []:
                    newtable.append(newrow)
            Report("join complete")
            return newtable
        # Execute and save fuzzy join comparison changes in memory
        joinedtable = fuzzyjoin()
        fields = joinedtable[0]
        self.fields = fields
        data = joinedtable[1:]
        self.readerobj = data
        # Aggregate multiple joins using aggregator and fieldmapping if mergematches is true
        if mergematches == True:
            allmainfieldstoagg = [ mainfield for eachjoinID in self.joinconditions for mainfield in self.joinconditions[eachjoinID]["mainfield"] ]
            Report("aggregating to "+str(allmainfieldstoagg))
            aggregator = Aggregator(table=self, aggunit=allmainfieldstoagg, aggfieldmapping=fieldmapping, displaydetails=self.displaydetails)
            agggregatedtable = aggregator.Run()
            # Remember aggregation in memory
            self.fields = agggregatedtable.fields
            self.readerobj = agggregatedtable.readerobj
        

    def keepfields(self, keepfields):
        """
        Changes the table to only keep the fields in the given list, deleting the rest.

        - keepfields: a list of fieldname strings to keep.
        """
        Report("keeping only selected fields")
        newtable = []
        newtable.append([eachfield for eachfield in self.fields if eachfield in keepfields])
        for rowindex in range(self.len):
            newtable.append([self.ReadRow(rowindex,eachfield) for eachfield in self.fields if eachfield in keepfields])
        self.fields = newtable[0]
        self.readerobj = newtable[1:]
        pass
    def deletefields(self, delfields):
        """
        Changes the table to delete the fields in the given list.

        - delfields: a list of fieldname strings to delete.
        """
        newtable = []
        newtable.append([eachfield for eachfield in self.fields if eachfield not in delfields])
        for rowindex in range(self.len):
            newtable.append([self.ReadRow(rowindex,eachfield) for eachfield in self.fields if eachfield not in delfields])
        self.fields = newtable[0]
        self.readerobj = newtable[1:]
        pass
    def addfields(self, addfields):
        """
        Adds additional fields to the table that can be written in later on.

        - addfields: a list of fieldname strings to add.
        """
        newtable = []
        toprows = self.fields
        toprows.extend(addfields)
        newtable.append(toprows)
        for rowindex in xrange(self.len):
            newrow = self.FetchEntireRow(rowindex)
            newrow.extend(["" for eachnewfield in addfields])
            newtable.append(newrow)
        self.fields = newtable[0]
        self.readerobj = newtable[1:]
        pass
    def setfields(self, fields):
        """
        Defines the table's fieldnames. Should only be used when creating a new table
        from scratch, or if one wants to rename all of the fields.

        - fields: a list of fieldname strings to use for the table.
        """
        self.fields = fields
    def addrow(self, row):
        """
        Add a row to the bottom of the table

        - row: a list of data values representing the row to add. It is up to you that
        these are in the same order as the fieldnames and has equal length.
        """
        self.readerobj.append(row)
    def writerow(self, row, field, value):
        """
        Writes a specific cell value

        - row: the row in which to write the value
        - field: the fieldname whose value will be written
        - value: the value to write
        """
        #determine field index
        if isinstance(field, int) == True:
            column = field
        elif isinstance(field, basestring) == True:
            column = self._findfieldnameindex(field)
        #write value
        self.readerobj[row][column] = value
    def add_uniqueid(self, idname):
        """
        Only used internally
        """
        self.addfields([idname])
        for rowid in xrange(self.len):
            self.writerow(rowid, idname, rowid)
    def createsplit(self, splitfields):
        """
        Splits the table based on unique values in one or more fields.
        A new table is created by grouping together all records that have
        the same value in all of the splitfields. All the new tables are
        returned as readymade table instances.
        Note: does not yet work for shapefiles...

        - splitfields: a list of fieldname strings on which to base the split. 
        """
        Report("splitting table")
        allsplits = dict()
        # then loop and split
        for rowindex in xrange(self.len):
            rowid = " ||| ".join([self.ReadRow(rowindex,eachsplit) for eachsplit in splitfields])
            # add new empty splitlist if not already there
            if rowid not in allsplits:
                newtable = Table()
                newtable.setfields(self.fields)
                allsplits.update( {rowid:newtable} )
            # add row to corresponding split id
            allsplits[rowid].addrow(self.FetchEntireRow(rowindex))
        Report("splitted into "+str(len(allsplits.keys()))+" new tables")
        return allsplits.values()
    def aggregate(self, groupby, fieldmapping):
        """
        Aggregates the table based on fieldmapping, grouped into categorical groupings

        - groupby: a list of fieldnames to use for making the categorical groupings
        - fieldmapping: a list of tuples. Each tuple has two items:
          - the first the name of a field
          - the second how to aggregate that field. Valid aggregation types are:
            - average
            - median
            - sum
            - standard deviation (not working yet)
            - count
            - most common
            - category count (not working yet)
            - category percent (not working yet)
        """
        Report("aggregating to "+str(groupby))
        aggregatedtable = aggregator.aggregate(table=self, groupby=groupby, fieldmapping=fieldmapping)
        return aggregatedtable
    #finished




##################
# MODULE FUNCTIONS
##################

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def load(filepath, xlsheetname=None):
    """
    Loads a file from a filepath, returning a table instance.

    - filepath: a string of the table's filepath, including file extension. Supported fileformats are:
      - .txt (for now only tab-delimited)
      - .xls/.xlsx (Excel spreadsheets)
      - .dbf/.shp
    - *xlsheetname: if the file is an Excel file, this option must be specified as a string of the sheetname to be loaded.
    """
    table = Table(filepath, xlsheetname=xlsheetname)
    return table
def new():
    """
    Creates an empty table instance that can be used to build from scratch
    """
    table = Table()
    return table
def mergetables(*mergetables):
    """
    Note: does not yet work for shapefiles...
    """
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
                    row.append( table.ReadRow(rowindex,field) )
                else:
                    row.append( "" )
            outtable.addrow(row)
    #return merged table
    return outtable




        
#########
# TESTING
#########
if __name__ == "__main__":

    try:
        os.mkdir("testresults")
    except:
        pass
    
    table1 = Table(r"D:\My Files\GIS Data\(Easy Georeferencer)\TestingGrounds\countries1980_table.txt")

##    print("testing tablejoin")
##    #create table2
##    table2 = Table()
##    table2.setfields(["Countries2","Comment"])
##    table2.addrow(["Zimbawe","Hello!!"])
##    #join
##    table1.add_joincondition(mainfield="Countries",joinfield="Countries2",matchpercent=90)
##    table1.createjoin(table2)
##    #save
##    table1.save("testresults/jointest.txt")
##
##    print("testing split")
##    for index,subtable in enumerate(table1.createsplit(["Countries"])):
##        subtable.save("testresults/subsplit"+str(index)+".txt")

    print("testing merge")
    table2 = Table(r"D:\My Files\GIS Data\(Easy Georeferencer)\TestingGrounds\(I.np.uts)\Some More Testdata\decme-clean.csv")
    mergedtable = mergetables(table1,table2)
    mergedtable.save("testresults/mergetest.txt")

    print("testing aggregate")
    aggregatedtable = table2.aggregate(groupby=["reginc"], fieldmapping=[("year","category count")])
    #aggregatedtable = table2.aggregate(groupby=["reginc","year"], fieldmapping=[("popurb","average")])
    aggregatedtable.save("testresults/aggtest.txt")

##    print("testing normal shapefile")
##    shapefiletable = Table(r"D:\Test Data\cshapes\cshapes.shp")
##    shapefiletable.save("C:/Users/BIGKIMO/Desktop/shapefilesave.shp")
##
##    print("testing shapefile merge")
##    shapefiletable2 = Table(r"D:\Test Data\cshapes\cshapes.shp")
##    mergedshapetable = mergetables(shapefiletable, shapefiletable2)
##    mergedshapetable.save("C:/Users/BIGKIMO/Desktop/mergedshapesave.shp")
    
    #print("heavy loading test")
    #import timetaker as timer
    #timer.start()
    #gadmpath = r"D:\My Files\GIS Data\General\Global Subadmins\gadm2.shp"
    #gadmtable = LoadFile(gadmpath)
    #timer.stop("load entire gadm table")
    



