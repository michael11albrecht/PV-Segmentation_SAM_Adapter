from PIL import Image
import numpy as np
import rasterio
from rasterio.transform import from_origin
import os
import cv2 as cv
from tqdm import tqdm

def saveGeotiff(image_path, geo_info, output_path):
    # Open the image and convert it to numpy array
    img = Image.open(image_path)
    numpy_img = np.array(img)
    numpy_img = cv.resize(numpy_img, (geo_info[4], geo_info[4]))
    binary_img = numpy_img > 0.5
    binary_img = binary_img.astype(int)
    binary_img = binary_img[:,:,0]

    # Create a transform using the geo_info
    # origin is the upper left corner of the image
    pixel_size = (geo_info[2]-geo_info[0])/binary_img.shape[1]
    transform = from_origin(geo_info[0], geo_info[1], pixel_size, pixel_size)

    #create folders if they don't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Create a new GeoTIFF file
    with rasterio.open(output_path, 'w', driver='GTiff', 
                       height=binary_img.shape[0], width=binary_img.shape[1], 
                       count=1, dtype=str(binary_img.dtype),
                       crs='+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs',
                       transform=transform) as dst:
        dst.write(binary_img, indexes=1)

def run_save_geotiff(pred_path, geo_info, output_path):
    for filename in tqdm(os.listdir(pred_path), desc="Saving GeoTIFFs"):
        clean_filename = filename.split('.')[0]
        file_geo_info = geo_info[clean_filename]
        saveGeotiff(os.path.join(pred_path, filename), file_geo_info, os.path.join(output_path, f'{clean_filename}.tif'))