import os
import rasterio
import numpy as np

def get_tiles(masks_path):
    tile_list = []
    for mask_filename in os.listdir(masks_path):
        if f'{mask_filename.split("_")[0]}_{mask_filename.split("_")[1]}' not in tile_list:
            tile_list.append(f'{mask_filename.split("_")[0]}_{mask_filename.split("_")[1]}')
    return tile_list

def get_split_tiles(masks_path, tile):
    split_tile_list = []
    for mask_filename in os.listdir(masks_path):
        if f'{mask_filename.split("_")[0]}_{mask_filename.split("_")[1]}' == tile:
            split_tile_list.append(mask_filename)
    return split_tile_list

def get_tile_data(mask_filename, filepath):
    with rasterio.open(f"{filepath}/{mask_filename}") as tif:
        tiff_coos = tif.bounds #xmin=0,ymin=1,xmax=2,ymax=3 (utm32)
        array = tif.read(1)
    return tiff_coos, array

def read_split_tiles(maskpath, tile):
    split_tile_list = get_split_tiles(maskpath, tile)
    split_tile_dict = {}
    for split_tile in split_tile_list:
        split_tile_dict[split_tile] = (get_tile_data(split_tile, maskpath))
    return split_tile_dict

def get_min_coords(split_tile_dict):
    min_coords_x = []
    min_coords_y = []
    for key in split_tile_dict:
        min_coords_x.append(split_tile_dict[key][0][0])
        min_coords_y.append(split_tile_dict[key][0][1])
    return (min(min_coords_x), min(min_coords_y))

def create_full_array(split_tile_dict, min_coords, tile_size_px, tile_size_m):
    utm2px = tile_size_px/tile_size_m
    full_array = np.zeros((tile_size_px, tile_size_px))
    for key in split_tile_dict:
        x_min_utm = split_tile_dict[key][0][0] - min_coords[0]
        y_min_utm = split_tile_dict[key][0][1] - min_coords[1]
        x_min = int(x_min_utm*utm2px)
        y_min = int(y_min_utm*utm2px)
        for y in range(split_tile_dict[key][1].shape[0]):
            for x in range(split_tile_dict[key][1].shape[1]):
                if split_tile_dict[key][1][x,y] == 1:
                    full_array[x_min+x,y_min+y] = 1
    return full_array

def calc_tile_area_px(full_array):
    area = np.sum(full_array)
    return area

def px_area_to_m2(area_px, tile_size_px, tile_size_m):
    return (area_px / (tile_size_px**2)) * tile_size_m**2

def calc_area(masks_path, tile, tile_size_px, tile_size_m):
    split_tile_dict = read_split_tiles(masks_path, tile)
    min_coords = get_min_coords(split_tile_dict)
    full_array = create_full_array(split_tile_dict, min_coords, tile_size_px, tile_size_m)
    area_px = calc_tile_area_px(full_array)
    area = px_area_to_m2(area_px, tile_size_px, tile_size_m)
    return area

def calc_whole_area(masks_path, tile_size_px, tile_size_m):
    tile_list = get_tiles(masks_path)
    area = 0
    for tile in tile_list:
        area += calc_area(masks_path, tile, tile_size_px, tile_size_m)
    return area

def main(masks_path, tile_size_px, tile_size_m):
    area = calc_whole_area(masks_path, tile_size_px, tile_size_m)
    print(f'{area}m^2 of the tiles is covered by PV.')
    print(f'{area/((tile_size_m**2)*len(get_tiles(masks_path)))}% of the tiles is covered by PV.')
    print(f'Calculated with 0.2kW/m^2 peak this would be {area*0.2}kW of peak power.')