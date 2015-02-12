
def to_file(table, savepath, **kwargs):
    encoding = kwargs.get("encoding")
    def encode(x):
        if isinstance(x, unicode):
            x = x.encode(encoding)
        else: x = repr(x)
        return x
    
    if savepath.lower().endswith(".txt"):
        writer = open(savepath, "w")
        fields = [encode(field.name) for field in table.fields]
        writer.write("\t".join(fields) + "\n")
        for row in table:
            rowvalues = map(encode, row)
            writer.write("\t".join(rowvalues) + "\n")
        writer.close()

    else:
        raise Exception("Fileformat not supported for saving to")
