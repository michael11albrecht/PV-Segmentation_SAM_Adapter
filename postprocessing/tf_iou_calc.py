import numpy as np
import os
from PIL import Image


import tensorflow.keras.metrics as metrics

def load_png2npy(png_path):
    if png_path.endswith(".png"):
        png = Image.open(png_path)
        png.load()
        np_array = np.asarray(png, dtype="int32")
        return np_array


def load_mask(pred_folderpath, true_folderpath):
    pred_masks = []
    true_masks = []
    for filename in os.listdir(pred_folderpath):
        if filename.endswith(".npy"):
            pred_masks.append(np.load(f"{pred_folderpath}/{filename}"))
            true_masks.append(load_png2npy(f"{true_folderpath}/{filename.split('.')[0]}.png"))
    return pred_masks, true_masks


def iou_calc(y_true, y_pred):
    m = metrics.IoU(num_classes=2, target_class_ids=[1])
    m.update_state(y_true, y_pred)
    return m.result().numpy()

def run(pred_folderpath, true_folderpath):
    pred_masks, true_masks = load_mask(pred_folderpath, true_folderpath)
    ious = []
    for i in range(len(pred_masks)):
        ious.append(iou_calc(true_masks[i], pred_masks[i]))
    
    print(f"Mean IoU: {np.mean(ious)}")


run('test/numpy','load/masks/test')