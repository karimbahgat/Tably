import journalism as j

class Table(j.Table):

    def __init__(self, rows, fields):
        fieldnames, fieldtypes = zip(*fields)
        j.Table.__init__(self, rows, fieldtypes, fieldnames)
        # rename some functions
        self.keepfields = self.select
        self.dropfields = "..."
        self.select = self.where
        self.exclude = "..."
        self.select_indexes = self.limit # maybe even make this into a builtin slice thingie
        self.unique = self.distinct
        self.sort = self.order_by

    # rename some attributes
    @property
    def fields(self):
        return zip(self.fieldnames, self.fieldtypes)
    @property
    def fieldtypes(self):
        return self.get_column_types()
    @property
    def fieldnames(self):
        return self.get_column_names()

    def join(self, left_key, table, right_key, keep="all"):
        if keep == "all":
            return self.left_outer_join(left_key, table, right_key)
        elif keep == "matches":
            return self.inner_join(left_key, table, right_key)

    def split(self, *splitfields):
        "allow split to take multiple fields, maybe even make more effective with itertools"
        self.group_by
        pass

    def aggregate(self, *aggregatefields):
        "allow aggregate to take multiple fields, maybe even make more effective with itertools"
        pass

    # add a bunch of new functionality

    # name
    # width
    # height aka __len__
    # __iter__
    # __str__
    # save
    # row and __get__
    # column and __get__
    # delete, add, insert, and replace fields and rows
    # duplicates
    # recode
    # membership
    # split_values, split_fieldnames, split_rowids, split_fieldnames_rowids
    # disaggregate??
    # relate
    # time extension
    # space extension

    # and some general functions

    # new
    # load (incl auto detect columntype)
    # merge
    
if __name__ == "__main__":
    import tably
    loaded = tably.load("/Users/karim/Desktop/pyGDELT/data/GDELT_working_EXCEL_wrapper.xlsx")
    texttype = j.TextType()
    jtable = Table(loaded.rows, [(field,texttype) for field in loaded.fields] )
    for v in jtable.columns: pass #print str(v)[:100]

    
