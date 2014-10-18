# Import main modules
import imp, csv, os, sys, time, pickle, traceback, difflib, datetime, codecs, operator, math, shutil, urllib, decimal
from math import *
# Import custom modules
from textual import txt
from messages import Report

#INTERNAL USE ONLY
class _AggregatorEngine:
    def __init__(self, table, aggunit, aggfieldmapping, interpolate=None, displaydetails=False):
        self.getaggunit = "not yet started"
        self.table = table
        self.aggunit = aggunit
        self.aggfieldmapping = dict(aggfieldmapping)
        self.aggvaluesdict = dict()
        for eachfield in self.aggfieldmapping.keys():
            self.aggvaluesdict.update( {eachfield:list()} )
        self.aggsummarydict = dict()
        self.interpolate = interpolate
        self.displaydetails = displaydetails
    def Feed(self, rowindex):
        # summarize old row if new agg
        self.oldgetaggunit = self.getaggunit
        if rowindex < self.table.len:
            self.getaggunit = " ||| ".join([ self.table.ReadRow(row=rowindex, field=eachaggunit) for eachaggunit in self.aggunit ])
        if (self.getaggunit != self.oldgetaggunit or rowindex == self.table.len) and self.oldgetaggunit != "not yet started": #the last part to avoid summarizing for first row
            Report("-----------------", self.displaydetails)
            Report(["new break aggunit", self.getaggunit], self.displaydetails)
            self.aggsummarydict.update( {self.oldgetaggunit:dict()} )
            # summarize old counting
            for eachfield in self.aggfieldmapping.keys():
                # only numbers summaries
                if self.aggfieldmapping[eachfield].lower() == "average":
                    summary = sum(self.aggvaluesdict[eachfield])/len(self.aggvaluesdict[eachfield])
                    self.aggsummarydict[self.oldgetaggunit].update( {eachfield:summary} )
                    Report([eachfield, "average", summary], self.displaydetails)
                    pass
                elif self.aggfieldmapping[eachfield].lower() == "median":
                    middleindex = len(self.aggvaluesdict[eachfield])/2
                    if isinstance(middleindex, int):
                        summary = self.aggvaluesdict[eachfield][middleindex]
                    else:
                        summary = self.aggvaluesdict[eachfield][int(middleindex-0.5)] + self.aggvaluesdict[eachfield][int(middleindex+0.5)]
                        summary = summary/2
                    self.aggsummarydict[self.oldgetaggunit].update( {eachfield:summary} )
                    Report([eachfield, "median", summary], self.displaydetails)
                    pass
                elif self.aggfieldmapping[eachfield].lower() == "sum":
                    summary = sum(self.aggvaluesdict[eachfield])
                    self.aggsummarydict[self.oldgetaggunit].update( {eachfield:summary} )
                    Report([eachfield, "sum", summary], self.displaydetails)
                    pass
                elif self.aggfieldmapping[eachfield].lower() == "standard deviation":
                    pass
                # general summaries
                elif self.aggfieldmapping[eachfield].lower() == "count":
                    summary = len(self.aggvaluesdict[eachfield])
                    self.aggsummarydict[self.oldgetaggunit].update( {eachfield:summary} )
                    Report([eachfield, "count", summary], self.displaydetails)
                    pass
                elif self.aggfieldmapping[eachfield].lower() == "most common":
                    summary = max(set(self.aggvaluesdict[eachfield]), key=self.aggvaluesdict[eachfield].count)
                    self.aggsummarydict[self.oldgetaggunit].update( {eachfield:summary} )
                    Report([eachfield, "most common", summary], self.displaydetails)
                elif self.aggfieldmapping[eachfield].lower() == "category count":
                    #NOTE: works except saves categories as a dict string, just need to find way to save each category to field of its own
                    sortedcategories = sorted(self.aggvaluesdict[eachfield])
                    categorysummaries = dict()
                    oldvalue = None
                    tempvaluelist = []
                    #collect for each category
                    for eachvalue in sortedcategories:
                        if oldvalue and eachvalue != oldvalue:
                            #new breakpoint
                            categorysummaries[eachfield+"_"+str(oldvalue)] = len(tempvaluelist)
                            tempvaluelist = []
                        tempvaluelist.append(eachvalue)
                        oldvalue = eachvalue
                    #collect for last category
                    categorysummaries[eachfield+"_"+str(eachvalue)] = len(tempvaluelist)
                    print(categorysummaries)
                    #then finally remember all category counts in dict...
                    categorysummaries = str(categorysummaries)
                    self.aggsummarydict[self.oldgetaggunit].update( {eachfield:categorysummaries} )
                elif self.aggfieldmapping[eachfield].lower() == "category percent":
                    pass
            # clear and repopulate empty counting lists
            self.aggvaluesdict.clear()
            for eachfield in self.aggfieldmapping.keys():
                self.aggvaluesdict.update( {eachfield:list()} )

        # feed current row, but not if beyond table, ie last summary
        if rowindex < self.table.len:
            for eachfield in self.aggfieldmapping.keys():
                valuelist = self.aggvaluesdict[eachfield]
                value = self.table.ReadRow(row=rowindex, field=eachfield)
                # convert nrs to float
                if self.aggfieldmapping[eachfield].lower() in ["sum", "average", "median"]:
                    try:
                        value = float(value)
                    except:
                        # set to zero if empty
                        if value == "":
                            value = 0.0
                        else:
                            Report([ "text value ignored because the aggregating method for this field requires numbers only", value, "type", str(type(value)) ], self.displaydetails)
                    pass
                # append value to list, but not text values if number summary
                if not isinstance(value, float) and self.aggfieldmapping[eachfield].lower() in ["sum", "average", "median"]:
                    pass
                else:
                    valuelist.append(value)
                    self.aggvaluesdict[eachfield] = valuelist

        # move cursor beyond last row to detect finish and summarize there too
        if rowindex+1 == self.table.len:
            self.Feed(rowindex+1)

    def Populate(self, rowindex):
        self.oldgetaggunit = self.getaggunit
        if rowindex < self.table.len:
            self.getaggunit = " ||| ".join([ self.table.ReadRow(row=rowindex, field=eachaggunit) for eachaggunit in self.aggunit ])
        # detect if new agg
        if (self.getaggunit != self.oldgetaggunit or rowindex == self.table.len) and self.oldgetaggunit != "not yet started": #the last part to avoid summarizing for first row
            Report("-----------------", self.displaydetails)
            Report(["new break aggunit", self.getaggunit], self.displaydetails)
            self.aggsummarydict.update( {self.oldgetaggunit:dict()} )
        # also move cursor beyond last row to detect finish and populate there too
        if rowindex+1 == self.table.len:
            self.Populate(rowindex+1)

    def Interpolate(self):
        # for each row
        for eachaggunit in self.aggsummarydict.keys():
            Report("-----------------", self.displaydetails)
            # set first interpolate value
            startinterpolatevalue = self.interpolate[1]
            endinterpolatevalue = self.interpolate[2]
            for aggfieldindex, eachaggfield in enumerate(self.aggunit):
                # find interpolate field
                if eachaggfield == self.interpolate[0]:
                    # add interpolated dict ids between start and end range
                    for eachinterpolate in range(int(float(startinterpolatevalue)), int(float(endinterpolatevalue))+1):
                        newaggunit = eachaggunit.split(" ||| ")
                        # copy aggid, change the interpolatevalue, and add to dict
                        newaggunit[aggfieldindex] = txt(float(eachinterpolate))
                        newaggunit = " ||| ".join(newaggunit)
                        Report(["interpolated", newaggunit], self.displaydetails)
                        self.aggsummarydict.update( {newaggunit:dict()} )
                        for eachfield in self.aggfieldmapping.keys():
                            if self.aggfieldmapping[eachfield].lower() in ["most common"]:
                                defaultvalue = ""
                            else:
                                defaultvalue = 0
                            self.aggsummarydict[newaggunit].update( {eachfield:defaultvalue} )
                    Report(["new break aggunit", eachaggunit], self.displaydetails)
                
    def Run(self):
        # sort table
        Report("sorting table", self.displaydetails)
        self.table.SortTable(self.aggunit, direction="down")

        # populate empty table
        Report("populating empty table", self.displaydetails)
        self.getaggunit = "not yet started"
        for rowindex in range(self.table.len):
            # feed info to aggregator
            self.Populate(rowindex=rowindex)

        # maybe interpolate aggunits before starting
        if self.interpolate != None:
            Report("interpolating selected break unit", self.displaydetails)
            if len(self.interpolate) == 3:
                # interpolate aggunits
                self.Interpolate()
            else:
                Report("error: Interpolate option requires a list of length 3")

        # loop and aggregate table
        Report("reading and aggregating table", self.displaydetails)
        self.getaggunit = "not yet started"
        for rowindex in range(self.table.len):
            # feed info to aggregator
            self.Feed(rowindex=rowindex)
            
        # create virtual table
        Report("making new table from results", self.displaydetails)
        self.virtualtable = []
        # first fields
        outputfieldnames = [eachaggunit for eachaggunit in self.aggunit]
        for eachfield in self.aggfieldmapping.keys():
            outputfieldnames.append(eachfield+"_"+self.aggfieldmapping[eachfield])
        self.virtualtable.append(outputfieldnames)
        # then values
        for eachaggunit in self.aggsummarydict.keys():
            newrow = eachaggunit.split(" ||| ")
            allsummaries = self.aggsummarydict[eachaggunit]
            for eachfield in self.aggfieldmapping.keys():
                summaryvalue = allsummaries[eachfield]
                newrow.append(summaryvalue)
            # encode before writing
            self.virtualtable.append(newrow)
            
        #create and return table instance
        import main
        aggregatedtable = main.Table(data=self.virtualtable)
        aggregatedtable.SortTable(self.aggunit, direction="down")
        Report("finished aggregating to new table", self.displaydetails)
        return aggregatedtable

#USER FUNCTIONS
def Aggregate(table, groupby, fieldmapping):
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
    aggengine = _AggregatorEngine(table=table, aggunit=groupby, aggfieldmapping=fieldmapping)
    aggregatedtable = aggengine.Run()
    return aggregatedtable

