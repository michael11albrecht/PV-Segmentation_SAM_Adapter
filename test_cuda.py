""" MIT License

Copyright (c) 2023 tianrun-chen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
 """

import argparse
import os

import yaml
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

import datasets
import models
import utils

from torchvision import transforms
from mmcv.runner import load_checkpoint

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np


def batched_predict(model, inp, coord, bsize):
    with torch.no_grad():
        model.gen_feat(inp)
        n = coord.shape[1]
        ql = 0
        preds = []
        while ql < n:
            qr = min(ql + bsize, n)
            pred = model.query_rgb(coord[:, ql: qr, :])
            preds.append(pred)
            ql = qr
        pred = torch.cat(preds, dim=1)
    return pred, preds


def tensor2PIL(tensor):
    toPIL = transforms.ToPILImage()
    return toPIL(tensor)


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def eval_psnr(loader, model, data_norm=None, eval_type=None, eval_bsize=None,
              verbose=False):
    model.eval()
    if data_norm is None:
        data_norm = {
            'inp': {'sub': [0], 'div': [1]},
            'gt': {'sub': [0], 'div': [1]}
        }

    if eval_type == 'f1':
        metric_fn = utils.calc_f1
        metric1, metric2, metric3, metric4 = 'f1', 'auc', 'none', 'none'
    elif eval_type == 'fmeasure':
        metric_fn = utils.calc_fmeasure
        metric1, metric2, metric3, metric4 = 'f_mea', 'mae', 'none', 'none'
    elif eval_type == 'ber':
        metric_fn = utils.calc_ber
        metric1, metric2, metric3, metric4 = 'shadow', 'non_shadow', 'ber', 'none'
    elif eval_type == 'cod':
        metric_fn = utils.calc_cod
        metric1, metric2, metric3, metric4 = 'sm', 'em', 'wfm', 'mae'

    val_metric1 = utils.Averager()
    val_metric2 = utils.Averager()
    val_metric3 = utils.Averager()
    val_metric4 = utils.Averager()

    pbar = tqdm(loader, leave=False, desc='val')
    nr = 0
    for batch in pbar:
        for k, v in batch.items():
            batch[k] = v.cuda()

        inp = batch['inp']

        pred = torch.sigmoid(model.infer(inp))

        cpu_pred = pred.cpu()
        vector_temp = cpu_pred.detach().squeeze().numpy()

        filepath = loader.dataset.dataset.dataset_1.files[nr]
        nr += 1
        last = filepath.split('/')[-1]
        file_name = last.split('.')[0]
        save_path_img = 'test/dv'
        save_path_np = 'test/numpy'
        try:
            np.save(f'{save_path_np}/{file_name}.npy',vector_temp)
            
        except:
            os.makedirs(save_path_np)
            np.save(f'{save_path_np}/{file_name}.npy',vector_temp)
        try:
            plt.imsave(f'{save_path_img}/{file_name}.png',vector_temp, cmap=cm.gray)
        except:
            os.makedirs(save_path_img)
            plt.imsave(f'{save_path_img}/{file_name}.png',vector_temp, cmap=cm.gray)

        result1, result2, result3, result4 = metric_fn(pred, batch['gt'])
        val_metric1.add(result1.item(), inp.shape[0])
        val_metric2.add(result2.item(), inp.shape[0])
        val_metric3.add(result3.item(), inp.shape[0])
        val_metric4.add(result4.item(), inp.shape[0])

        if verbose:
            pbar.set_description('val {} {:.4f}'.format(metric1, val_metric1.item()))
            pbar.set_description('val {} {:.4f}'.format(metric2, val_metric2.item()))
            pbar.set_description('val {} {:.4f}'.format(metric3, val_metric3.item()))
            pbar.set_description('val {} {:.4f}'.format(metric4, val_metric4.item()))

    return val_metric1.item(), val_metric2.item(), val_metric3.item(), val_metric4.item()


if __name__ == '__main__':
    with torch.no_grad():
        parser = argparse.ArgumentParser()
        parser.add_argument('--config')
        parser.add_argument('--model')
        parser.add_argument('--prompt', default='none')
        args = parser.parse_args()
    
        with open(args.config, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        spec = config['test_dataset']
        dataset = datasets.make(spec['dataset'])
        dataset = datasets.make(spec['wrapper'], args={'dataset': dataset})
        loader = DataLoader(dataset, batch_size=spec['batch_size'],
                            num_workers=8)
    
        model = models.make(config['model']).cuda()
        sam_checkpoint = torch.load(args.model, map_location='cuda:0')
        model.load_state_dict(sam_checkpoint, strict=True)
        
        metric1, metric2, metric3, metric4 = eval_psnr(loader, model,
                                                       data_norm=config.get('data_norm'),
                                                       eval_type=config.get('eval_type'),
                                                       eval_bsize=config.get('eval_bsize'),
                                                       verbose=True)
        print('metric1: {:.4f}'.format(metric1))
        print('metric2: {:.4f}'.format(metric2))
        print('metric3: {:.4f}'.format(metric3))
        print('metric4: {:.4f}'.format(metric4))