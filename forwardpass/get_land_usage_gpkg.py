import fiona
from shapely.geometry import shape, box
from shapely.strtree import STRtree
import pickle
from datetime import datetime
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
    

def getLandUse(bbox, lk_tree, lk):
    # List of land use types that are considered usable (all of kind "Siedlung")
    use_list = ['Wohnbaufläche','Industrie- und Gewerbefläche','Halde','Bergbaubetrieb',
                'Tagebau, Grube Steinbruch','Fläche gemischter Nutzung','Fläche besonderer funktionaler Prägung',
                'Sport-, Freizeit- und Erholungsfläche','Friedhof']

    #find all layers (LK) that intersect the bbox
    lk_matches = lk_tree.query(bbox)
    
    lks = []
    for match in lk_matches:
        lks.append(lk[match][0])

    for lk in lks:
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
        matches = inner_tree.query(bbox)
        for match in matches:
            if use_types[match] in use_list:
                return True

    return False

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

def checkGeoList(geo_list, img_path):
    download_gpkg('forwardpass/data/alkis')
    lk_tree, lk = getLkTree()
    for f_name, bbox in geo_list.items():
        needed = getLandUse(bbox[0:3], lk_tree, lk)
        if not needed:
            os.remove(f'{img_path}/{f_name}.png')
        

#test
bbox = (597627, 5292841, 597704, 5293004)
bbox2 = (642652.25, 5365025.75, 642671.28, 5365071.72)
bbox3 = (691478.00, 5337490.00, 691500.00, 5337510.00)
bbox = box(*bbox3)

start = datetime.now()

download_gpkg('forwardpass/data/alkis')
lk_tree, lk = getLkTree()
print(getLandUse(bbox, lk_tree, lk))

print(datetime.now() - start)