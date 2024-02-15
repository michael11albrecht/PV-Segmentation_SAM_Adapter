import fiona
from shapely.geometry import shape, box
from shapely.strtree import STRtree
import pickle
from tqdm import tqdm
import os
import requests

def download_gpkg(out_dir):
    """
    Downloads the shapefile.
    """
    url = 'https://geodaten.bayern.de/odd/m/3/daten/tn/Nutzung_kreis.gpkg'
    filename = url.split('/')[-1]
    out_file = os.path.join(out_dir, filename)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)        
    if not os.path.exists(out_file):
        print(f'Downloading {filename} about 5GB')
        r = requests.get(url, allow_redirects=True, stream=True)
        total = int(r.headers.get('content-length', 0))
        with open(out_file, 'wb') as file, tqdm(
                desc=f'Downloading {filename}',
                total=total,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
        ) as bar:
            for data in r.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)
    else:
        print(f'File {out_file} already exists, skipping download.')

def buildLKTree():
    lk = []
    for layer in fiona.listlayers('forwardpass/data/alkis/Nutzung_kreis.gpkg'):
        lk.append((layer,fiona.open('forwardpass/data/alkis/Nutzung_kreis.gpkg', layer=layer).bounds))
    lk_tree = STRtree([box(*bounds) for layer, bounds in lk])
    return lk_tree, lk
    

def getInnerTree(lk):
    geoms = []
    use_types = []
    with fiona.open('forwardpass/data/alkis/Nutzung_kreis.gpkg', layer=lk) as src:
        for feature in src:
            geoms.append(shape(feature['geometry']))
            use_types.append(feature['properties']['nutzart'])

    #create spatial index for geoms
    tree = STRtree(geoms)
    return tree, use_types
    
def findLks(bbox, lk_tree, lk):
    #find all layers (LK) that intersect the bbox
    lk_matches = lk_tree.query(bbox)
    
    lks = []
    for match in lk_matches:
        lks.append(lk[match][0])
    return lks

def loadInnerTree(lk):
    #load inner tree and use_types or create them if they don't exist
    try:
        with open(f'forwardpass/data/alkis/tree_{lk}.pkl', 'rb') as f:
            inner_tree = pickle.load(f)
        with open(f'forwardpass/data/alkis/use_{lk}.pkl', 'rb') as f:
            use_types = pickle.load(f)
    except:
        inner_tree, use_types = getInnerTree(lk)
        with open(f'forwardpass/data/alkis/tree_{lk}.pkl', 'wb') as f:
            pickle.dump(inner_tree, f)
        with open(f'forwardpass/data/alkis/use_{lk}.pkl', 'wb') as f:
            pickle.dump(use_types, f)
    return inner_tree, use_types

def getLandUse(bbox, inner_tree, use_types):
    # List of land use types that are considered usable (all of kind "Siedlung")
    use_list = ['Wohnbaufläche','Industrie- und Gewerbefläche',
                'Fläche gemischter Nutzung','Fläche besonderer funktionaler Prägung',
                'Sport-, Freizeit- und Erholungsfläche']

    matches = inner_tree.query(bbox)
    found_matches = len(matches) > 0
    for match in matches:
        if use_types[match] in use_list:
            return True, found_matches
    return False, found_matches

def getLkTree():
    #load lk_tree and lk or create them if they don't exist
    try:
        with open('forwardpass/data/alkis/lk_tree.pkl', 'rb') as f:
            lk_tree = pickle.load(f)
        with open('forwardpass/data/alkis/lk.pkl', 'rb') as f:
            lk = pickle.load(f)
    except:
        lk_tree, lk = buildLKTree()
        with open('forwardpass/data/alkis/lk_tree.pkl', 'wb') as f:
            pickle.dump(lk_tree, f)
        with open('forwardpass/data/alkis/lk.pkl', 'wb') as f:
            pickle.dump(lk, f)
    return lk_tree, lk

def checkLandRemove(bbox, inner_tree, use_types, img_path, f_name):
    needed, found_match = getLandUse(box(*bbox), inner_tree, use_types)
    if found_match and not needed:
        os.remove(f'{img_path}/{f_name}.png')
    return found_match

def checkGeoList(geo_list, img_path):
    download_gpkg('forwardpass/data/alkis')
    lk_tree, lk_bb = getLkTree()
    inner_tree = None
    use_types = None
    t_use = 0
    for f_name, bbox in tqdm(geo_list.items(), desc='Checking land usage'):
        lks = findLks(box(*bbox[0:4]), lk_tree, lk_bb)
        if lks in inner_tree.keys():
            for lk in lks:
                use_types[lk] = (t_use, use_types[lk])
                t_use += 1
                checkLandRemove(bbox[0:4], inner_tree[lk], use_types[lk], img_path, f_name)
        else:
            for lk in lks:
                new_inner_tree, new_use_types = loadInnerTree(lk)
                inner_tree[lk] = new_inner_tree
                use_types[lk] = (t_use, new_use_types)
                t_use += 1
                checkLandRemove(bbox[0:4], inner_tree[lk], use_types[lk], img_path, f_name)
                if len(use_types) > 4:
                    min_key = min(use_types, key=lambda k: use_types[k][0])
                    del inner_tree[min_key]
                    del use_types[min_key]
        