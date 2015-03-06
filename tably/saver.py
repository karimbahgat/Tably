
import csv

from .fileformats import xlwt
from .builder import MISSING

def to_file(table, savepath, **kwargs):
    
    encoding = kwargs.get("encoding")
    def encode(x):
        if x == MISSING:
            x = ""
        else:
            if isinstance(x, unicode):
                x = x.encode(encoding)
            else: x = repr(x)
        return x
    
    if savepath.lower().endswith(".txt"):
        fileobj = open(savepath, "w")
        writer = csv.writer(fileobj, delimiter='\t')
        # write column names
        fields = [encode(field.name) for field in table.fields]
        writer.writerow(fields)
        # write rows
        for row in table:
            rowvalues = map(encode, row)
            writer.writerow(rowvalues)
        fileobj.close()

    elif savepath.lower().endswith(".xls"):
        workbook = xlwt.Workbook(encoding=encoding)
        sheet = workbook.add_sheet("Sheet1")
        # write column names
        for field in table.fields:
            sheet.write(r=0, c=field.i, label=encode(field.name) )
        # write rows
        for row in table:
            for fieldindex,val in enumerate(row):
                sheet.write(r=row.i+1, c=fieldindex, label=encode(val) )
        # save
        workbook.save(savepath)
        
    else:
        raise Exception("Fileformat not supported for saving to")
