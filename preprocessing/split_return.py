from PIL import Image
import numpy as np
import os
from pathlib import Path
import rasterio
from tqdm import tqdm

#only tested with 2500x2500 to 1024x1024 images
class Split:
    def __init__(self, in_size = 2500, dest_size = 1024, artificial_overlap = 0):
        self.dest_size_ = dest_size
        self.in_size_ = in_size
        if artificial_overlap < 1 and artificial_overlap >= 0:
            self.artificial_overlap_ = artificial_overlap
        else:
            raise ValueError('Artificial overlap must be between 0 and 0.99 (1 would mean 100pct overlap)')
        self.split_coos_ = self.calcSplit(self.in_size_)

    
    def calcSplit(self, width_height):
        #only one calculation because working with squared formats
        #calculating the overlap on each side (half_overlap)
        #calculating an artificial overlap to based on input 0-0.99 to create more trainings images
        px_artificial_overlap = int(self.dest_size_*self.artificial_overlap_)
        art_left = self.dest_size_-px_artificial_overlap
        t = width_height//art_left
        left = width_height%art_left
        total_overlap = art_left-left
        overlap = (total_overlap//t)+px_artificial_overlap

        split_coos = []

        for r in range(t):
            for c in range(t):
                #xmin,ymin,xmax,ymax
                split_coos.append((c*self.dest_size_-c*overlap,r*self.dest_size_-r*overlap,(c+1)*self.dest_size_-c*overlap,(r+1)*self.dest_size_-r*overlap))
            #to make sure that the whole image is covered (columns)    
            split_coos.append((width_height-self.dest_size_,r*self.dest_size_-r*overlap,width_height,(r+1)*self.dest_size_-r*overlap))
        #to make sure that the whole image is covered (rows)
        for c in range(t):
                split_coos.append((c*self.dest_size_-c*overlap,width_height-self.dest_size_,(c+1)*self.dest_size_-c*overlap,width_height))
        #bottom right corner
        split_coos.append((width_height-self.dest_size_,width_height-self.dest_size_,width_height,width_height))
        
        return split_coos
    

    def splitImages(self, image_filepath):
        images = []
        geo_infos = {}
        for filename in tqdm(os.listdir(image_filepath), desc="Splitting images"):
            im = Image.open(f"{image_filepath}/{filename}")
            tiff = rasterio.open(f"{image_filepath}/{filename}")
            tiff_coos = tiff.bounds #xmin=0,ymin=1,xmax=2,ymax=3 (utm32)
            q = 0
            for coos in self.split_coos_:
                image_name = filename.split('.')[0]
                image = im.crop(coos)
                images.append((image,image_name,q))
                geo_infos.update(self.splitImgGeoInfo(f'{image_name}_{q}_', tiff_coos, coos))
                q += 1
        
        return images, geo_infos
    
    def splitMask(self, mask_filepath):
        masks = []
        for filename in os.listdir(mask_filepath):
            mask = np.load(f"{mask_filepath}/{filename}")
            q = 0
            for coos in self.split_coos_:
                mask_name = filename.split('.')[0]
                new_mask = mask[coos[1]:coos[3],coos[0]:coos[2]]
                masks.append((new_mask,mask_name,q))
                q += 1
        
        return masks

    

    def splitBoundingBox(self, bounding_box, image_id):

        new_bounding_box = {}
        q = 0
        for coos in self.split_coos_:
            #possibility that box between new image tiles --> only in the image which contains the whole box could be changed?
            if bounding_box[0] > coos[0] and bounding_box[1] > coos[1] and bounding_box[2] < coos[2] and bounding_box[3] < coos[3]:
                  new_bounding_box[f"{image_id}_{q}"] = (bounding_box[0]-coos[0],bounding_box[1]-coos[1],bounding_box[2]-coos[0],bounding_box[3]-coos[1])
            q += 1
        return new_bounding_box
    
    def splitImgGeoInfo(self, image_name, tiff_coos, coos):
        
        x_min = (coos[0]/self.in_size_) * (tiff_coos[2]-tiff_coos[0]) + tiff_coos[0]
        y_min = -(coos[1]/self.in_size_) * (tiff_coos[3]-tiff_coos[1]) + tiff_coos[3]
        x_max = (coos[2]/self.in_size_) * (tiff_coos[2]-tiff_coos[0]) + tiff_coos[0]
        y_max = -(coos[3]/self.in_size_) * (tiff_coos[3]-tiff_coos[1]) + tiff_coos[3]

        split_img_coos = {image_name: (x_min, y_min, x_max, y_max, self.dest_size_)}

        return split_img_coos
        