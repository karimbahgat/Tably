
class _Loader:
    def __init__(self, filepath):
        if filepath.endswith(".shp"):
            # use shapefile module
            pass
        elif filepath.endswith((".geojson",".geo.json",".json")):
            # use pygeoj module
            pass
        elif filepath.endswith(".kml"):
            # use fastkml module
            pass
        elif filepath.endswith(".wkt"):
            # use pygeoif module
            pass
        else:
            raise Exception("fileformat not supported")
