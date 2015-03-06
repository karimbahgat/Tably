import Tkinter as tk

class VerticalScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling
    """
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)            

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)

def view(tablytable):
    # NOTE: maybe instead make a custom-canvas with custom scrollers
    # that simply calculate their position in the table and continually
    # creates labels for those rows on the fly, so it can load tables
    # of any size.
    window = tk.Tk()
    
    fields = tablytable.fields
    rows = tablytable.rows
    
    # first fields
    fieldframe = tk.Frame(window)
    fieldframe.grid(row=0, column=0, columnspan=len(fields))
    for findex,field in enumerate(fields):
        fieldlabel = tk.Label(fieldframe, width=9, text=str(field), bg="dark grey", relief="groove")
        fieldlabel.pack(side="left") #.grid(row=0, column=findex)
    canvasframe = VerticalScrolledFrame(window) #tk.Frame(window) #ScrollableCanvas(window, _mode="xy")
    canvasframe.grid(row=1, rowspan=60, column=0, columnspan=len(fields))

    # then cells
    for rindex,row in enumerate(rows):
        for cindex,val in enumerate(row):
            cell = tk.Label(canvasframe.interior, width=9, text=str(val), relief="groove")
            cell.grid(row=rindex, column=cindex)

    #canvasframe.canvas.config(scrollregion=canvasframe.canvas.bbox(tk.ALL) )

    window.mainloop()




#######################################################################

# MAYBE BEST?

import Tkinter as tk
import time

class TableView(tk.Frame):
    def __init__(self, master, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        self.cellwidth = 40
        self.cellheight = 20
        self.screencorner = (0,0)
        self.table = None
        def update_view(event):
            self.update_view()
        self.after(100, self.update_view)
        #self.resized = time.time()
        #self.bind("<Configure>", update_view)

        # place scrollbars
##        def verticalscrollbarpressed(event):
##            sliderclicked = event.widget.identify(event.x, event.y)
##            print sliderclicked
##            if sliderclicked == "slider":
##                event.widget.dragging = True
##        def verticalscrollbarreleased(event):
##            if event.widget.dragging == True:
##                print event.widget.get()
##                rel_slidertop = event.widget.get()[1]
##                rel_viewtop = rel_slidertop / float(self.totalheight)
##                rel_viewbottom = (rel_slidertop + self.viewheight) / float(self.totalheight)
##                print rel_viewtop, rel_viewbottom
##                event.widget.set(rel_viewtop, rel_viewbottom)
##                event.widget.dragging = False


                
        def vertical_yview(eventtype, rel_slidertop):
            if eventtype == "moveto":
                # move tableview
                curcol,currow = self.screencorner
                topcell = self.totalheight * float(rel_slidertop)
                bottomcell = topcell + self.viewheight
                midcell = sum([topcell,bottomcell]) / 2.0
                print midcell
                #self.scroll_to_cell(column=curcol, row=int(round(midcell)))
                # reanchor scrollbar
                rel_sliderbottom = bottomcell / float(self.totalheight)
                self.verticalscrollbar.set(rel_slidertop, rel_sliderbottom)
            
        self.verticalscrollbar = tk.Scrollbar(self,
                                              repeatinterval=2000,
                                              repeatdelay=2000)
        self.verticalscrollbar.config(command=vertical_yview)
        self.verticalscrollbar.pack(side="right", fill="y")
        #self.verticalscrollbar.bind("<Button-1>", verticalscrollbarpressed)
        #self.verticalscrollbar.bind("<ButtonRelease-1>", verticalscrollbarreleased)
        self.tablearea = tk.Frame(self)
        self.tablearea.pack(side="left", fill="both", expand=True)
        
        #self.horizontalscrollbar = tk.Scrollbar(self.tablearea, orient=tk.HORIZONTAL)
        #self.horizontalscrollbar.pack(side="bottom", fill="x")
        #...

    def set_data(self, data):
        self.fields = data.pop(0)
        self.data = data

    @property
    def totalwidth(self):
        return len(self.data[0])

    @property
    def totalheight(self):
        return len(self.data)

    @property
    def viewwidth(self):
        screenpixelwidth = self.winfo_width()
        cells_in_screenwidth = screenpixelwidth / float(self.cellwidth)
        actual_cells = min(cells_in_screenwidth, self.totalwidth)
        return int(round(actual_cells))

    @property
    def viewheight(self):
        screenpixelheight = self.winfo_height()
        cells_in_screenheight = screenpixelheight / float(self.cellheight)
        cells_in_screenheight -= 1 # to make room for one row of fields
        actual_cells = min(cells_in_screenheight, self.totalheight)
        return int(round(actual_cells))

    def scroll_by_cells(self, columns, rows):
        curcol,currow = self.screencorner
        self.screencorner = int(curcol + columns), int(currow + rows)
        self.update_view()

    def scroll_by_percent(self, colperc, rowperc):
        columns = self.totalwidth * colperc
        rows = self.totalheight * rowperc
        self.scroll_by_cells(columns, rows)
        
    def scroll_to_cell(self, column, row):
        self.screencorner = int(column), int(row)
        self.update_view()

    def scroll_to_percent(self, colperc, rowperc):
        column = self.totalwidth * colperc
        row = self.totalheight * rowperc
        self.scroll_to_cell(column, row)

    def update_view(self):
        oldtable = self.table
    
        # make new table
        print "upperleft cell:", self.screencorner
        print "windowsize, pixels:", self.winfo_width(), self.winfo_height()
        print "windowsize, cells:", self.viewwidth, self.viewheight
        curcol,currow = self.screencorner
        self.table = tk.Frame(self.tablearea)
        rowslice = slice(currow, currow + self.viewheight)
        colslice = slice(curcol, curcol + self.viewwidth)
        for f,field in enumerate(self.fields[colslice]):
            cellframe = tk.Frame(self.table, width=self.cellwidth, height=self.cellheight)
            cellframe.grid(column=f, row=0)
            cellframe.grid_propagate(False)
            cell = tk.Label(cellframe, bg="black", fg="white")
            cell.place(relwidth=1, relheight=1)
            cell["text"] = field
        for r,row in enumerate(self.data[rowslice]):
            r += 1
            for c,value in enumerate(row[colslice]):
                cellframe = tk.Frame(self.table, width=self.cellwidth, height=self.cellheight)
                cellframe.grid(column=c, row=r)
                cellframe.grid_propagate(False)
                cell = tk.Entry(cellframe)
                cell.place(relwidth=1, relheight=1)
                cell.insert(0, value)
        self.table.place(relwidth=1, relheight=1)
                
        # finally, destroy old table
        if oldtable:
            oldtable.destroy()


if __name__ == "__main__":
    
    w,h = 40,1000
    data = [["f%i"%i for i in range(w)]]
    data += [["%i,%i"%(col,row) for col in range(w)] for row in range(h)]

    window = tk.Tk()
    tableview = TableView(window, width=400, height=200)
    tableview.pack(fill="both", expand=True)
    tableview.set_data(data)
    print "table total dims", tableview.totalwidth, tableview.totalheight
    
    tk.Button(window, text="Refresh", command=tableview.update_view).pack()
    def testmove():
        tableview["width"] += 20
        tableview["height"] += 20
        tableview.scroll_by_percent(0.10, 0.10)
    tk.Button(window, text="Test move", command=testmove).pack()

    window.mainloop()


