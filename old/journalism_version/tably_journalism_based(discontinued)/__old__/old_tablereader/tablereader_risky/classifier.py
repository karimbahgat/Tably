"""
Classifier
Submodule of tablereader.

Classifies a set of input values into different groupings.
Still not finished completely.

Copyright 2014 Karim Bahgat
"""

class _SymbolClass:
    def __init__(self, classmin, classmax, minvalue, maxvalue, classvalue, classsymbol):
        "_min and _max are not attr values meant for user, but used for membership determination internally and can be different from attr"
        self._min = classmin
        self._max = classmax
        self.min = minvalue
        self.max = maxvalue
        self.classvalue = classvalue
        self.classsymbol = classsymbol

class _Classifier:
    """
Internal use only
A classifier that holds a set of instructions on how to classify a shapefile's visual symbols based on its attribute values. 
The classifier can hold multiple classifications, one for each symbol (e.g. fillsize and fillcolor), and these are added with the AddClassification method. 
When a layer is passed to a rendering operations its classifier is used as the recipe on how to symbolize the shapefile. 
This classifier is also needed to render a shapefile's legend.

*Takes no arguments*

"""
    def __init__(self):
        self.values = dict()
        self.symbols = dict()
        self.allclassifications = []
        self.name = "unnamed classifier"
    def AddClassification(self, symboltype, valuefield, symbolrange=None, classifytype="equal interval", nrclasses=5):        
        if not symbolrange and classifytype!="categorical":
            raise TypeError("since you have chosen a gradual classification you must specify a range of symbol values to choose from")
        classification = dict([("symboltype",symboltype),
                               ("valuefield",valuefield),
                               ("symbolrange",symbolrange),
                               ("classifytype",classifytype),
                               ("nrclasses",nrclasses) ])
        self.allclassifications.append(classification)
    def AddCustomClass(self, symboltype, valuefield, valuemin, valuemax):
        #first loop through existing classes and delete/reset maxmin values to make room for the new class value range
        #then create and insert class at appropriate position
        pass
    def AddValue(self, index, symboltype, value):
        if self.values.get(index):
            #add to dict if already exits
            self.values[index][symboltype] = value
        else:
            #or create new dict if not
            self.values[index] = dict([(symboltype, value)])
        self.symbols[index] = dict()
    def CalculateClasses(self, classification):
        classifytype = classification.get("classifytype")
        #calculate classes based on classifytype
        if classifytype.lower() == "categorical":
            self._UniqueCategories(classification)
            self.__AssignMembershipByUnique(classification)
        elif classifytype.lower() == "equal interval":
            self._EqualInterval(classification)
            self.__AssignMembershipByValue(classification)
        elif classifytype.lower() == "equal classes":
            self._EqualClasses(classification)
            self.__AssignMembershipByIndex(classification)
        elif classifytype.lower() == "natural breaks":
            self._NaturalBreaks(classification)
            self.__AssignMembershipByValue(classification)
        else:
            raise TypeError("classifytype must be one of: ...")
    def GetSymbol(self, uniqid, symboltype):
        #for each class test value for membership
        featuresymbols = self.symbols.get(uniqid)
        if featuresymbols:
            symbol = featuresymbols.get(symboltype)
            if symbol:
                return symbol
    def GetValues(self):
        return self.sortedvalues
    def GetClassifications(self):
        return self.allclassifications

    # INTERNAL USE ONLY
    def __AssignMembershipByValue(self, classification):
        symboltype = classification.get("symboltype")
        classes = classification.get("classes")
        #loop through values and assign class symbol to each for the specified symboltype
        for uniqid, value in self.sortedvalues:
            value = value[symboltype]
            #for each class test value for membership
            for eachclass in classes:
                #membership true if within minmax range of that class
                if value >= eachclass._min and value <= eachclass._max:
                    #assign classsymbol
                    self.symbols[uniqid][symboltype] = eachclass.classsymbol
                    break
    def __AssignMembershipByIndex(self, classification):
        symboltype = classification.get("symboltype")
        classes = classification.get("classes")
        #loop through values and assign class symbol to each for the specified symboltype
        for index, (uniqid, value) in enumerate(self.sortedvalues):
            value = value[symboltype]
            #for each class test value for membership
            for eachclass in classes:
                #membership true if within minmax range of that class
                if index >= eachclass._min and index <= eachclass._max:
                    #assign classsymbol
                    self.symbols[uniqid][symboltype] = eachclass.classsymbol
                    break
    def __AssignMembershipByUnique(self, classification):
        symboltype = classification.get("symboltype")
        classes = (each for each in classification.get("classes"))
        #loop through values and assign class symbol to each for the specified symboltype
        oldvalue = None
        for index, (uniqid, value) in enumerate(self.sortedvalues):
            value = value[symboltype]
            if value != oldvalue:
                eachclass = next(classes)
            self.symbols[uniqid][symboltype] = eachclass.classsymbol
            oldvalue = value
    def __CustomSymbolRange(self, classification):
        symbolrange = classification.get("symbolrange")
        nrclasses = classification.get("nrclasses")
        #first create pool of possible symbols from raw inputted symbolrange
        if isinstance(symbolrange[0], (int,float)):
            #create interpolated or shrinked nr range
            symbolrange = listy.Resize(symbolrange, nrclasses)
        elif isinstance(symbolrange[0], basestring):
            #create color gradient by blending color rgb values
            rgbcolors = [colour.hex2rgb(eachhex) for eachhex in symbolrange]
            rgbgradient = listy.Resize(rgbcolors, nrclasses)
            symbolrange = [colour.rgb2hex(eachrgb) for eachrgb in rgbgradient]
            #alternative color spectrum hsl interpolation
            ###rgbcolors = [colour.rgb2hsl(colour.hex2rgb(eachhex)) for eachhex in symbolrange]
            ###rgbgradient = listy.Resize(rgbcolors, nrclasses)
            ###symbolrange = [colour.rgb2hex(colour.hsl2rgb(eachrgb
        #update classification with new symbolrange
        classification["symbolrange"] = symbolrange
    def _UniqueCategories(self, classification):
        """
Remember, with unique categories the symbolrange doesn't matter, and only works for colors
"""
        symboltype = classification.get("symboltype")
        classifytype = classification.get("classifytype")
        if not "color" in symboltype:
            raise TypeError("the categorical classification can only be used with color related symboltypes")
        #initiate
        self.sortedvalues = sorted([(uniqid, value) for uniqid, value in self.values.iteritems()], key=operator.itemgetter(1))
        sortedvalues = [value[symboltype] for uniqid,value in self.sortedvalues]
        #populate classes
        classes = []
        #then set symbols
        olduniq = None
        for index, uniq in enumerate(sortedvalues):
            if uniq != olduniq:
                classsymbol = Color("random")
                classmin = uniq
                classmax = uniq
                minvalue = classmin
                maxvalue = classmax
                #create and add class
                classes.append( _SymbolClass(classmin, classmax, minvalue, maxvalue, index, classsymbol) )
                olduniq = uniq
        classification["classes"] = classes
    def _EqualInterval(self, classification):
        symboltype = classification.get("symboltype")
        symbolrange = classification.get("symbolrange")
        classifytype = classification.get("classifytype")
        nrclasses = classification.get("nrclasses")
        #initiate
        self.__CustomSymbolRange(classification)
        symbolrange = classification["symbolrange"]
        self.sortedvalues = sorted([(uniqid, value) for uniqid, value in self.values.iteritems()], key=operator.itemgetter(1))
        sortedvalues = [value[symboltype] for uniqid,value in self.sortedvalues]
        lowerbound = sortedvalues[0]
        upperbound = sortedvalues[-1]
        intervalsize = int( (upperbound-lowerbound)/float(nrclasses) )        
        #populate classes
        classmin = lowerbound
        classes = []
        for index, classsymbol in enumerate(symbolrange):
            if index == nrclasses-1:
                classmax = upperbound
            else:
                classmax = classmin+intervalsize
            #determine min and max value
            minvalue = classmin
            maxvalue = classmax
            #create and add class
            classes.append( _SymbolClass(classmin, classmax, minvalue, maxvalue, index, classsymbol) )
            #prep for next
            classmin = classmax
        classification["classes"] = classes
    def _EqualClasses(self, classification):
        symboltype = classification.get("symboltype")
        symbolrange = classification.get("symbolrange")
        classifytype = classification.get("classifytype")
        nrclasses = classification.get("nrclasses")
        #initiate
        self.__CustomSymbolRange(classification)
        symbolrange = classification["symbolrange"]
        self.sortedvalues = sorted([(uniqid, value) for uniqid, value in self.values.iteritems()], key=operator.itemgetter(1))
        sortedvalues = [value[symboltype] for uniqid,value in self.sortedvalues]
        classsize = int( len(sortedvalues)/float(nrclasses) )
        #populate classes
        classmin = 0
        classes = []
        for index, classsymbol in enumerate(symbolrange):
            if index == nrclasses-1:
                classmax = len(sortedvalues)-1
            else:
                classmax = classmin+classsize
            #determine min and max value
            minvalue = sortedvalues[classmin]
            maxvalue = sortedvalues[classmax]
            #create and add class
            classes.append( _SymbolClass(classmin, classmax, minvalue, maxvalue, index, classsymbol) )
            #prep for next
            classmin = classmax
        classification["classes"] = classes
    def _NaturalBreaks(self, classification):
        symboltype = classification.get("symboltype")
        symbolrange = classification.get("symbolrange")
        classifytype = classification.get("classifytype")
        nrclasses = classification.get("nrclasses")
        #initiate
        self.__CustomSymbolRange(classification)
        symbolrange = classification["symbolrange"]
        self.sortedvalues = sorted([(uniqid, value) for uniqid, value in self.values.iteritems()], key=operator.itemgetter(1))
        sortedvalues = [value[symboltype] for uniqid,value in self.sortedvalues]
        lowerbound = sortedvalues[0]
        upperbound = sortedvalues[-1]
        def getJenksBreaks(dataList, numClass ):
            "taken from http://danieljlewis.org/files/2010/06/Jenks.pdf"
            dataList = sorted(dataList)
            #in mat1, populate empty classlists of zeros
            zeros = [0 for j in xrange(0,numClass+1)]
            zeroandones = [0]
            zeroandones.extend([1 for i in xrange(1,numClass+1)])
            mat1 = [list(zeros), zeroandones]
            mat1.extend([list(zeros) for i in xrange(2,len(dataList)+1)])
            #...while classes in element 1 are set to 1, except for first class which remains zero
            for i in xrange(1,numClass+1):
                mat1[1][i] = 1
            #in mat2, classes in element 0 and 1 are set to 0
            mat2 = [list(zeros),list(zeros)]
            #...while the classes in elements 2 and up are set to infinity, except for first class which is a zero
            mat2classes = [0]
            mat2classes.extend([float('inf') for i in xrange(1,numClass+1)])
            mat2ext = [list(mat2classes) for j in xrange(2,len(dataList)+1)]
            mat2.extend(mat2ext)
            #then the main work (everything prior to this has been optimized/changed from original code)
            v = 0.0
            for l in xrange(2,len(dataList)+1):
                s1 = 0.0
                s2 = 0.0
                w = 0.0
                for m in xrange(1,l+1):
                    i3 = l - m + 1
                    val = float(dataList[i3-1])
                    s2 += val * val
                    s1 += val
                    w += 1
                    v = s2 - (s1 * s1) / w
                    i4 = i3 - 1
                    if i4 != 0:
                        for j in xrange(2,numClass+1):
                            if mat2[l][j] >= (v + mat2[i4][j - 1]):
                                mat1[l][j] = i3
                                mat2[l][j] = v + mat2[i4][j - 1]  
                mat1[l][1] = 1
                mat2[l][1] = v         
            k = len(dataList)
            kclass = []
            for i in xrange(0,numClass+1):
                kclass.append(dataList[0])
            kclass[numClass] = float(dataList[-1])
            countNum = numClass
            while countNum >= 2:
                #print "rank = " + str(mat1[k][countNum])
                id = int((mat1[k][countNum]) - 2)
                #print "val = " + str(dataList[id])
                kclass[countNum - 1] = dataList[id]
                k = int((mat1[k][countNum] - 1))
                countNum -= 1
            return kclass
        #populate classes
        highthresh = 1000
        if len(sortedvalues) > highthresh:
            #the idea of using random sampling for large datasets came from a blogpost by Carson Farmer. I just added the idea of calculating the breaks several times and using the sample means for the final break values.
            #see: http://www.carsonfarmer.com/2010/09/adding-a-bit-of-classification-to-qgis/
            allrandomsamples = []
            samplestotake = 6
            for _ in xrange(samplestotake):
                randomsample = sorted(random.sample(sortedvalues, highthresh))
                randomsample[0] = lowerbound
                randomsample[-1] = upperbound
                tempbreaks = getJenksBreaks(randomsample, nrclasses)
                allrandomsamples.append(tempbreaks)
            jenksbreaks = [sum(allbreakvalues)/float(len(allbreakvalues)) for allbreakvalues in itertools.izip(*allrandomsamples)]
        else:
            jenksbreaks = getJenksBreaks(sortedvalues, nrclasses)
        breaksgen = (each for each in jenksbreaks[1:])
        classmin = lowerbound
        classes = []
        for index, classsymbol in enumerate(symbolrange):
            classmax = next(breaksgen)
            #determine min and max value
            minvalue = classmin
            maxvalue = classmax
            #create and add class
            classes.append( _SymbolClass(classmin, classmax, minvalue, maxvalue, index, classsymbol) )
            #prep for next
            classmin = classmax
        classification["classes"] = classes
