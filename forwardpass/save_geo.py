from PIL import Image
import numpy as np
import rasterio
from rasterio.transform import from_origin
import os

def saveGeotiff(image_path, geo_info, output_path):
    # Open the image and convert it to numpy array
    img = Image.open(image_path)
    numpy_img = np.array(img)

    # Create a transform using the geo_info
    # origin is the upper left corner of the image
    pixel_size = numpy_img.shape[1]/(geo_info[2]-geo_info[0])
    transform = from_origin(geo_info[0], geo_info[3], pixel_size, pixel_size)

    # Create a new GeoTIFF file
    with rasterio.open(output_path, 'w', driver='GTiff', 
                       height=numpy_img.shape[0], width=numpy_img.shape[1], 
                       count=1, dtype=str(numpy_img.dtype),
                       crs='+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs',
                       transform=transform) as dst:
        dst.write(numpy_img, 1)

def run_save_geotiff(pred_path, geo_info, output_path):
    for filename in os.listdir(pred_path):
        clean_filename = filename.split('.')[0]
        file_geo_info = geo_info[clean_filename]
        saveGeotiff(os.path.join(pred_path, filename), file_geo_info, os.path.join(output_path, f'{filename}.tif'))