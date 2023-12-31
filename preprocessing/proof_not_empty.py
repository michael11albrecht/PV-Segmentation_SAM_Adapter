import os
from PIL import Image 
import numpy as np
import random

class Proof:

    def __init__(self, img_path, mask_path):
        self.img_path_ = img_path
        self.mask_path_ = mask_path

    def is_empty_del(self, pct_empty=0.1):
        #pcr_empty is the percentage of images that are allowed to be empty
        deleted_images = 0
        total_images = 0
        not_empty_img = 0
        empty_img = []
        for mask_filename in os.listdir(self.mask_path_):
            mask_filepath = os.path.join(self.mask_path_, mask_filename)
            mask_png = Image.open(mask_filepath)
            mask_np = np.asarray(mask_png)
            if mask_np.sum() < 20:
                empty_img.append(mask_filename)
            else:
                not_empty_img += 1
            total_images += 1

        img_to_stay = int((not_empty_img*pct_empty))
        for _ in range(img_to_stay):
            empty_img.pop(random.randrange(0,len(empty_img)))

        for filename in empty_img:
            mask_filepath = os.path.join(self.mask_path_,filename)
            os.remove(mask_filepath)
            img_filepath = os.path.join(self.img_path_,filename)
            os.remove(img_filepath)
            deleted_images += 1

        print(f'total deleted images {deleted_images} of {total_images}, {img_to_stay} are empty')