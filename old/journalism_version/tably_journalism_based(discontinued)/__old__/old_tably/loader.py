import csv
from . import fileformats
from fileformats import xlrd
from fileformats import shapefile as pyshp
from fileformats import PyDTA


def from_file(filepath, delimiter=None, xlsheetname="Sheet1"):
    # determine filetype
    if filepath.endswith("txt"):
        filetype = "txt"
    elif filepath.endswith("csv"):
        filetype = "csv"
    elif filepath.endswith(("xls", "xlsx")):
        filetype = "excel"
    elif filepath.endswith(".dbf"):
        filetype = "dbf"
    elif filepath.endswith(".shp"):
        filetype = "shp"
    elif filepath.endswith(".dta"):
        filetype = "dta"
    elif filepath.endswith(".sav"):
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
        rows = [[eachcell for eachcell in eachrow] for eachrow in rows]
        fields = rows.pop(0)
    elif filetype == "excel":
        workbook = xlrd.open_workbook(filepath)
        excelobj = workbook.sheet_by_name(xlsheetname)
        rows = [ [excelobj.cell_value(row, column) for column in range(excelobj.ncols)] for row in range(1, excelobj.nrows)]
        fields = [ excelobj.cell_value(0, column) for column in range(excelobj.ncols) ]
    elif filetype == "dbf" or filetype == "shp":
        redirectpathtodbf = "/".join(filepath.split(".")[:-1])+".dbf"
        fileobj = open(redirectpathtodbf, 'rb')
        shapereader = pyshp.Reader(dbf=fileobj)
        rows = [ [eachcell for eachcell in eachrecord] for eachrecord in shapereader.iterRecords()]
        fields = [eachfieldlist[0] for eachfieldlist in shapereader.fields[1:]]
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
        fields = [eachvar for eachvar in spssreader.varNames]
    elif filetype == "dta":
        fileobj = open(filepath, "rb")
        statareader = PyDTA.StataTools.Reader(fileobj, missing_values=False)
        rows = [ [eachcell for eachcell in statareader[rowi] ] for rowi in xrange(len(statareader))]
        fields = [eachvar.name for eachvar in statareader.variables()]
    return fields, rows

def from_list(lists):
    rows = [[cell for cell in row] for row in lists]
    fields = [cell for cell in lists[0]]
    return fields, lists
