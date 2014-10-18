# Import main modules
import decimal

import sys
PYTHON3 = int(sys.version[0]) == 3
if PYTHON3:
    basestring = str
    unicode = str

def txt(obj, encoding="utf-8"):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            try:
                obj = unicode(obj, encoding)
            except:
                obj = unicode(obj, "latin") #backup encoding to decode into
    else:
        try:
            obj = str(float(obj))
        except:
            obj = str(obj)
    return obj

def encode(obj, encoding="utf-8", strlen=150, floatlen=16, floatprec=6):
    try:
        #encode as decimal nr
        float(obj)
        decimal.getcontext().prec = floatprec
        obj = str(decimal.Decimal(str(obj))) [:floatlen]
    except:
        #encode as text
        try:
            obj = obj.encode(encoding)
        except:
            obj = obj.encode("latin") #backup encoding to encode as
    return obj

