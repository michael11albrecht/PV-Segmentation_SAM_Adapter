import os
import rasterio
import numpy as np

def get_tiles(masks_path):
    tile_list = []
    for mask_filename in os.listdir(masks_path):
        if f'{mask_filename.split('_')[0]}_{mask_filename.split('_')[1]}' not in tile_list:
            tile_list.append(f'{mask_filename.split('_')[0]}_{mask_filename.split('_')[1]}')
    return tile_list

def get_split_tiles(masks_path, tile):
    split_tile_list = []
    for mask_filename in os.listdir(masks_path):
        if f'{mask_filename.split('_')[0]}_{mask_filename.split('_')[1]}' == tile:
            split_tile_list.append(mask_filename)
    return split_tile_list

def get_tile_coords(mask_filename, filepath):
    with rasterio.open(f"{filepath}/{mask_filename}") as tif:
        tiff_coos = tif.bounds #xmin=0,ymin=1,xmax=2,ymax=3 (utm32)
        array = tif.read()
    return tiff_coos, array

def read_split_tiles(maskpath, tile):
    split_tile_list = get_split_tiles(maskpath, tile)
    split_tile_dict = {}
    for split_tile in split_tile_list:
        split_tile_dict[split_tile] = (get_tile_coords(split_tile, maskpath))
    return split_tile_dict

def get_min_coords(split_tile_dict):
    min_coords_x = []
    min_coords_y = []
    for key in split_tile_dict:
        min_coords_x.append(split_tile_dict[key][0][0])
        min_coords_y.append(split_tile_dict[key][0][1])
    return (min(min_coords_x), min(min_coords_y))

def create_full_array(split_tile_dict, min_coords, tile_size_land):
    full_array = np.zeros((tile_size_land, tile_size_land))
    for key in split_tile_dict:
        x_min = split_tile_dict[key][0][0] - min_coords[0]
        y_min = split_tile_dict[key][0][1] - min_coords[1]
        full_array[y_min:y_min+split_tile_dict[key][1].shape[0], x_min:x_min+split_tile_dict[key][1].shape[1]] = \
        max(full_array[y_min:y_min+split_tile_dict[key][1].shape[0], x_min:x_min+split_tile_dict[key][1].shape[1]], split_tile_dict[key][1])
    return full_array

def calc_tile_area(full_array, tile_size_land):
    area = 0
    for y in range(tile_size_land):
        for x in range(tile_size_land):
            if full_array[y,x] == 1:
                area += 1
    return area

def calc_area(masks_path, tile, tile_size_land):
    split_tile_dict = read_split_tiles(masks_path, tile)
    min_coords = get_min_coords(split_tile_dict)
    full_array = create_full_array(split_tile_dict, min_coords, tile_size_land)
    area = calc_tile_area(full_array, tile_size_land)
    return area

def main():
    masks_path = "forwardpass/data/geotiff"
    tile = "32598_5292"
    tile_size_land = 1000
    area = calc_area(masks_path, tile, tile_size_land)
    print(area)