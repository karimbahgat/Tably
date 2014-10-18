import sys, os, itertools

from . import _loader

class Table(Table):
    "this extension adds space awareness to the table's rows"
    
    def make_spatial(coords=None, geometrytype=None):
        "coords is an expression based on fieldnames that define a list of vertexes"
        self.bbox = ""
        for row in self:
            # make fields into vars
            codelines = []
            for field in seld.fields:
                codelines.append("%s = %s"%(field,row[self.fields.index(field)]))
            # run and retrieve query value
            coordslistquery = "[%s]"%coords
            codelines.append(coordslistquery)
            code = "\n".join(codelines)
            #
            row.geometry = exec(code)
            row.bbox = ""

    @property
    def is_spatial(self):
        pass
    
