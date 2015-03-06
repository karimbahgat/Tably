import csv
from . import fileformats
from fileformats import xlrd
from fileformats import shapefile as pyshp
from fileformats import PyDTA


def from_file(filepath, delimiter=None, xlsheetname=None):
    
    # determine filetype
    if filepath.lower().endswith(".txt"):
        filetype = "txt"
    elif filepath.lower().endswith(".csv"):
        filetype = "csv"
    elif filepath.lower().endswith((".xls", ".xlsx")):
        filetype = "excel"
    elif filepath.lower().endswith(".dbf"):
        filetype = "dbf"
    elif filepath.lower().endswith(".shp"):
        filetype = "shp"
    elif filepath.lower().endswith(".dta"):
        filetype = "dta"
    elif filepath.lower().endswith(".sav"):
        filetype = "spss"
    else:
        raise TypeError("Could not create a table from the given filepath: the filetype extension is either missing or not supported")
    
    # import data and retrieve fieldnames
    if filetype in ("txt","csv"):
        fileobj = open(filepath, 'rU')
        if delimiter == None:
            dialect = csv.Sniffer().sniff(fileobj.read())
            fileobj.seek(0)
            rows = csv.reader(fileobj, dialect)
        else:
            rows = csv.reader(fileobj, delimiter=delimiter)
        rows = [eachrow for eachrow in rows]
        fieldtuples = [(varname,"",None,dict()) for varname in rows.pop(0)]
        
    elif filetype == "excel":
        workbook = xlrd.open_workbook(filepath)
        if not xlsheetname: excelobj = workbook.sheet_by_index(0)
        else: excelobj = workbook.sheet_by_name(xlsheetname)
        rows = [excelobj.row_values(rowi,0,excelobj.ncols) for rowi in xrange(1, excelobj.nrows)]
        fieldtuples = [ (fieldname,"",None,dict()) for fieldname in excelobj.row_values(0,0,excelobj.ncols )]

    elif filetype == "dbf" or filetype == "shp":
        redirectpathtodbf = "/".join(filepath.split(".")[:-1])+".dbf"
        fileobj = open(redirectpathtodbf, 'rb')
        shapereader = pyshp.Reader(dbf=fileobj)
        rows = [ eachrecord for eachrecord in shapereader.iterRecords()]
        fieldtuples = [(varname,"",vartype,dict()) for varname,vartype,_,_ in shapereader.fields[1:]]
        # maybe treat types according to column types
        
    elif filetype == "spss":
        spssreader = savReaderWriter.SavReader(filepath)
        spssvalueLabels = spssreader.valueLabels
        rows = []
        for r, eachrow in enumerate(spssreader):
            labeledrow = []
            for i, eachvalue in enumerate(eachrow):
                try:
                    label = spssvalueLabels[spssvarNames[i]][eachvalue]
                except:
                    label = eachvalue
                labeledrow.append(label)
            rows.append(labeledrow)
        fieldtuples = [(varname,varlabel,vartype,valuelabels) for varname,varlabel,vartype,valuelabels in zip(spssreader.varNames,spssreader.varLabels,spssreader.varTypes,spssreader.valueLabels)]
        # maybe treat types according to column types
        
    elif filetype == "dta":
        fileobj = open(filepath, "rb")
        statareader = PyDTA.StataTools.Reader(fileobj, missing_values=False)
        rows = [ [eachcell for eachcell in statareader[rowi] ] for rowi in xrange(len(statareader))]
        fieldtuples = [(eachvar.name,eachvar.label,eachvar.type,dict()) for eachvar in statareader.variables()]
        # maybe treat types according to column types
        
    return fieldtuples, rows

def from_list(lists):   
    fieldtuples = [(varname,"",None,dict()) for varname in lists[0]]
    rows = [[cell for cell in row] for row in lists[1:]]
    
    return fieldtuples, rows



