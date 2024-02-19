import sys
import os

#adding path to the some modules
for modules in ['preprocessing', 'postprocessing']:
    path = os.path.abspath(modules)
    sys.path.append(path)

from download_open_data import DownloadOpenData
from split_return import Split
from save_img_mask import Save
from ma_make_overlay import *
import argparse
from save_geo import run_save_geotiff
from get_land_usage_gpkg import checkGeoList
from calc_area import main as calc_area

def run(lat_1, lon_1, lat_2, lon_2, config, model, output_folder):
    download_ = DownloadOpenData()
    download_.wgs84_download(lat_1, lon_1, lat_2, lon_2, f'{output_folder}/tiles_download')

    split = Split(2500, 256)
    images, geo_infos = split.splitImages(f'{output_folder}/tiles_download')

    save_ = Save()
    save_.saveImg(f'{output_folder}/split_img', images, '')

    checkGeoList(geo_infos, f'{output_folder}/split_img')

    os.system(f'python fw_cuda.py --config {config} --model {model} --output_dir {output_folder}/pred_masks')

    run_overlay(f'{output_folder}/split_img', f'{output_folder}/pred_masks/png', f'{output_folder}/overlay')

    run_save_geotiff(f'{output_folder}/pred_masks/png', geo_infos, f'{output_folder}/geotiff')

    calc_area(f'{output_folder}/geotiff', 2500, 1000)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lat_1', type=float)
    parser.add_argument('--lon_1', type=float)
    parser.add_argument('--lat_2', type=float)
    parser.add_argument('--lon_2', type=float)
    parser.add_argument('--config', type=str, default='configs/ma_B_cuda.yaml')
    parser.add_argument('--model', type=str)
    parser.add_argument('--output_folder', type=str, default='forwardpass/data')

    args = parser.parse_args()

    lat_1 = args.lat_1
    lon_1 = args.lon_1
    lat_2 = args.lat_2
    lon_2 = args.lon_2
    config = args.config
    model = args.model
    output_folder = args.output_folder

    run(lat_1, lon_1, lat_2, lon_2, config, model, output_folder)