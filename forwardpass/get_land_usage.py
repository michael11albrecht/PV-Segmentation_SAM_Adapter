import shapefile as shp
import os
import requests
from tqdm import tqdm
import json

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

def Overlaps(bbox1, bbox2):
    """
    Returns True if bbox1 and bbox2 overlap.
    """
    if (bbox1[0] <= bbox2[0] <= bbox1[2] and bbox1[1] <= bbox2[1] <= bbox1[3])\
        or (bbox1[0] <= bbox2[2] <= bbox1[2] and bbox1[1] <= bbox2[3] <= bbox1[3])\
            or (bbox1[0] <= bbox2[0] <= bbox1[2] and bbox1[1] <= bbox2[3] <= bbox1[3])\
                or (bbox1[0] <= bbox2[2] <= bbox1[2] and bbox1[1] <= bbox2[1] <= bbox1[3]):
        return True
    else:
        return False
    
def create_search_tree(shapefile):
    """
    Creates a search tree for the shapefile.
    """
    splits = 4
    tree = {}
    threshold_x = (shapefile.bbox [2] - shapefile.bbox [0]) / (splits/2) + shapefile.bbox [0]
    threshold_y = (shapefile.bbox [3] - shapefile.bbox [1]) / (splits/2) + shapefile.bbox [1]

    #create tree
    tree[shapefile.bbox[0],shapefile.bbox[1],threshold_x,threshold_y] = {}
    tree[shapefile.bbox[0],threshold_y,threshold_x,shapefile.bbox[3]] = {}
    tree[threshold_x,shapefile.bbox[1],shapefile.bbox[2],threshold_y] = {}
    tree[threshold_x,threshold_y,shapefile.bbox[2],shapefile.bbox[3]] = {}

    #add shapes to tree
    for shape in tqdm(shapefile.shapeRecords(), desc='Creating search tree'):
        #bottom left
        if shape.shape.bbox[0] <= threshold_x:
            if shape.shape.bbox[1] <= threshold_y:
                #q3
                tree[shapefile.bbox[0],shapefile.bbox[1],threshold_x,threshold_y].update({tuple(shape.shape.bbox):shape.record.nutzart})
            else:
                #q2
                tree[shapefile.bbox[0],threshold_y,threshold_x,shapefile.bbox[3]].update({tuple(shape.shape.bbox):shape.record.nutzart})
        else:
            if shape.shape.bbox[1] <= threshold_y:
                #q4
                tree[threshold_x,shapefile.bbox[1],shapefile.bbox[2],threshold_y].update({tuple(shape.shape.bbox):shape.record.nutzart})
            else:
                #q1
                tree[threshold_x,threshold_y,shapefile.bbox[2],shapefile.bbox[3]].update({tuple(shape.shape.bbox):shape.record.nutzart})
        #top right
        if shape.shape.bbox[2] <= threshold_x:
            if shape.shape.bbox[3] <= threshold_y:
                #only in q3
                pass
            else:
                #q2
                tree[shapefile.bbox[0],threshold_y,threshold_x,shapefile.bbox[3]].update({tuple(shape.shape.bbox):shape.record.nutzart})
        else:
            if shape.shape.bbox[3] <= threshold_y:
                #q4
                tree[threshold_x,shapefile.bbox[1],shapefile.bbox[2],threshold_y].update({tuple(shape.shape.bbox):shape.record.nutzart})
            else:
                #q1
                tree[threshold_x,threshold_y,shapefile.bbox[2],shapefile.bbox[3]].update({tuple(shape.shape.bbox):shape.record.nutzart})
    return tree
        



def find_usetype_inside_bb(bbox, use_list, search_tree):
    """
    Returns the type of use of the shape object that contains the point (x,y).
    """
    use = False
    found = False
    for key in tree.keys():
        if Overlaps(key, bbox):
            found = True
            for key2 in tree[key].keys():
                if Overlaps(key2, bbox):
                    found = True
                    if check_if_usable(tree[key][key2], use_list):
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


def get_alkis_url(bbox,read_dir):
    """
    Returns the url of the alkis shapefile.
    """
    with open(f'{read_dir}/lk_list.json', 'r') as fp:
        lk_list = json.load(fp)

    dl_list = []
    for key, value in lk_list.items():
        if Overlaps(value, bbox):
            dl_list.append((key,f"https://download1.bayernwolke.de/a/tn/lkr/{key}.zip"))
    return dl_list


def download_shapefile(dl_list, out_dir):
    """
    Downloads the shapefile.
    """
    for url in tqdm(dl_list, desc='Downloading shapefile'):
        filename = url[1].split('/')[-1]
        out_file = os.path.join(out_dir, filename)
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)        
        if not os.path.exists(out_file):
            r = requests.get(url[1], allow_redirects=True)
            open(out_file, 'wb').write(r.content)
        else:
            print(f'File {out_file} already exists, skipping download.')

def make_lk_list(shapefile_dir, out_dir):
    """
    Creates a list of all shapefiles + boundingboxes
    """
    lk_list = {}
    for file in os.listdir(shapefile_dir):
        if file.endswith(".zip"):
            shapefile = load_shapefile(file[:-4])
            lk_list.update({file[:-4]:tuple(shapefile.bbox)})
    with open(f'{out_dir}/lk_list.json', 'w') as fp:
        json.dump(lk_list, fp)

def check_geolist(split_coos_list):
    """
        Checks which tiles are useful and which are not.
    """

    #load shapefile
    dl_list = set()
    for img in split_coos_list.values():
        dl_list.add(get_alkis_url([img[0],img[1],img[2],img[3]],'forwardpass/data'))
    #download shapefile
    download_shapefile(dl_list, "forwardpass/data/alkis")

    
    
    

#test
bbox = [597627, 5292841, 597704, 5293004]
dl_list = get_alkis_url(bbox,'forwardpass/data')
download_shapefile(dl_list, "forwardpass/data/alkis")
for file in dl_list:
    shapefile = load_shapefile(file[0])
    tree = create_search_tree(shapefile)
    print(find_usetype_inside_bb([597627, 5292841, 597704, 5293004], use_list, tree))
    print(find_usetype_inside_bb([597327, 5292841, 597304, 5293004], use_list, tree))

#get list of all shapefiles
make_lk_list("forwardpass/data/alkis", "forwardpass/data")