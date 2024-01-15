import shapefile as shp

# List of land use types that are considered usable (all of kind "Siedlung")
use_list = ['Wohnbaufläche','Industrie- und Gewerbefläche','Halde','Bergbaubetrieb',
            'Tagebau, Grube Steinbruch','Fläche gemischter Nutzung','Fläche besonderer funktionaler Prägung',
            'Sport-, Freizeit- und Erholungsfläche','Friedhof']



def load_shapefile(foldername):
    """
    Loads the shapefile and returns a GeoDataFrame.
    """
    return shp.Reader(f"forwardpass/data/alkis/{foldername}.zip")


def find_usetype_point(shapefile, x,y):
    """
    Returns the type of use of the shape object that contains the point (x,y).
    """
    for shape in shapefile.shapeRecords():
        if shape.shape.bbox[0] <= x <= shape.shape.bbox[2] and shape.shape.bbox[1] <= y <= shape.shape.bbox[3]:
            return shape.record.nutzart
        
    raise Exception(f"Point ({x},{y}) not in shapefile.")


def find_usetype_inside_bb(shapefile, bbox, use_list):
    """
    Returns the type of use of the shape object that contains the point (x,y).
    """
    use = False
    found = False
    for shape in shapefile.shapeRecords():
        if (bbox[0] <= shape.shape.bbox[0] <= bbox[2] and bbox[1] <= shape.shape.bbox[1] <= bbox[3])\
            or (bbox[0] <= shape.shape.bbox[2] <= bbox[2] and bbox[1] <= shape.shape.bbox[3] <= bbox[3]):
            found = True
            if check_if_usable(shape.record.nutzart, use_list):
                use = True
    if found == False:
        raise Exception(f"Bbox ({bbox[0]},{bbox[1]}) not in shapefile.")
    return use
        

def check_if_usable(usetype, use_list):
    """
    Returns True if the type of use of the shape object that contains the point (x,y) is in use_list.
    """
    if usetype in use_list:
        return True
    else:
        return False


#test    
#print(find_usetype_inside_bb(load_shapefile('tn_09780'),[597627, 5292841, 597704, 5293004], use_list))