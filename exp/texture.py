from __future__ import print_function
from __future__ import division

import os.path as osp
import sys
sys.path.append(osp.dirname(osp.dirname(osp.abspath(__file__))))

import numpy as np
import argparse
import gpflowSlim as gfs
from gpflowSlim.neural_kernel_network import NKNWrapper, NeuralKernelNetwork

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import tensorflow as tf
import copy
import os

import sys
from data.hparams import HParams
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)
DATA_PATH = os.path.join(root_path, 'data/DATA')

from utils.create_logger import create_logger, makedirs
from data import get_data
from utils.functions import median_distance_local
from kernels import KernelWrapper

FLOAT_TYPE=gfs.settings.float_type
# Training settings
parser = argparse.ArgumentParser(description='PyTorch Neural-Kernel-Network')
parser.add_argument('--data', type=str, default="plate", help='choose data')
parser.add_argument('--kern', type=str, default='nkn')
args = parser.parse_args()

#logger = create_logger('results/texture/' + args.data, 'logging', __file__)
#logger.info('----------------use {}-----------------'.format(args.kern))

############################## NKN info ##############################
def NKNInfo(x_train, idx):
    period = 0.1
    ls = median_distance_local(x_train1).astype(FLOAT_TYPE)
    ls[abs(ls) < 1e-6] = 1.

    nkn_var, sm_var = 0.1, 0.2
    kernel = dict(
        nkn=[
            {'name': 'RBF',      'params': {'input_dim': 1, 'lengthscales': ls, 'variance': nkn_var, 'name': 'k'+idx+'0'}},
            {'name': 'Linear',   'params': {'input_dim': 1, 'variance': nkn_var, 'name': 'k'+idx+'1'}},
            {'name': 'RatQuad',  'params': {'input_dim': 1, 'alpha': 1.0, 'variance': nkn_var, 'lengthscales': ls, 'name': 'k'+idx+'2'}},
            {'name': 'Periodic', 'params': {'input_dim': 1, 'lengthscales': ls, 'period': period, 'variance': nkn_var, 'name': 'k'+idx+'3'}}],
        sm=[
        {'name': 'SM', 'params':{'params': [
            {'w': np.float64(1./10), 'name': 'mixture0',
             'rbf': {'input_dim': 1, 'lengthscales': ls,      'variance': sm_var, 'name': 'SM-RBF0'},
             'cos': {'input_dim': 1, 'lengthscales': ls,      'variance': sm_var, 'name': 'SM-Cos0'}},
            {'w': np.float64(1./10), 'name': 'mixture1',
             'rbf': {'input_dim': 1, 'lengthscales': ls / 2,  'variance': sm_var, 'name': 'SM-RBF1'},
             'cos': {'input_dim': 1, 'lengthscales': ls / 2,  'variance': sm_var, 'name': 'SM-Cos1'}},
            {'w': np.float64(1./10), 'name': 'mixture2',
             'rbf': {'input_dim': 1, 'lengthscales': ls * 2,  'variance': sm_var, 'name': 'SM-RBF2'},
             'cos': {'input_dim': 1, 'lengthscales': ls * 2,  'variance': sm_var, 'name': 'SM-Cos2'}},
            {'w': np.float64(1./10), 'name': 'mixture3',
             'rbf': {'input_dim': 1, 'lengthscales': ls * 3,  'variance': sm_var, 'name': 'SM-RBF3'},
             'cos': {'input_dim': 1, 'lengthscales': ls * 3,  'variance': sm_var, 'name': 'SM-Cos3'}},
            {'w': np.float64(1./10), 'name': 'mixture4',
             'rbf': {'input_dim': 1, 'lengthscales': ls / 2,  'variance': sm_var, 'name': 'SM-RBF4'},
             'cos': {'input_dim': 1, 'lengthscales': ls / 2,  'variance': sm_var, 'name': 'SM-Cos4'}},
            {'w': np.float64(1./10), 'name': 'mixture5',
             'rbf': {'input_dim': 1, 'lengthscales': ls * 8,  'variance': sm_var, 'name': 'SM-RBF5'},
             'cos': {'input_dim': 1, 'lengthscales': ls * 8,  'variance': sm_var, 'name': 'SM-Cos5'}},
            {'w': np.float64(1./10), 'name': 'mixture6',
             'rbf': {'input_dim': 1, 'lengthscales': ls * 4,  'variance': sm_var, 'name': 'SM-RBF6'},
             'cos': {'input_dim': 1, 'lengthscales': ls * 4,  'variance': sm_var, 'name': 'SM-Cos6'}},
            {'w': np.float64(1./10), 'name': 'mixture7',
             'rbf': {'input_dim': 1, 'lengthscales': ls * 16, 'variance': sm_var, 'name': 'SM-RBF7'},
             'cos': {'input_dim': 1, 'lengthscales': ls * 16, 'variance': sm_var, 'name': 'SM-Cos7'}},
            {'w': np.float64(1./10), 'name': 'mixture8',
             'rbf': {'input_dim': 1, 'lengthscales': ls / 4,  'variance': sm_var, 'name': 'SM-RBF8'},
             'cos': {'input_dim': 1, 'lengthscales': ls / 4,  'variance': sm_var, 'name': 'SM-Cos8'}},
            {'w': np.float64(1./10), 'name': 'mixture9',
             'rbf': {'input_dim': 1, 'lengthscales': ls / 8,  'variance': sm_var, 'name': 'SM-RBF9'},
             'cos': {'input_dim': 1, 'lengthscales': ls / 8,  'variance': sm_var, 'name': 'SM-Cos9'}}],
            'name': 'SM'+idx}}]
    )[args.kern]

    wrapper = dict(
        nkn=[
            {'name': 'Linear',  'params': {'input_dim': 4, 'output_dim': 8, 'name': 'layer'+idx+'1'}},
            {'name': 'Product', 'params': {'input_dim': 8, 'step': 2,       'name': 'layer'+idx+'2'}},
            {'name': 'Linear',  'params': {'input_dim': 4, 'output_dim': 4, 'name': 'layer'+idx+'3'}},
            {'name': 'Product', 'params': {'input_dim': 4, 'step': 2,       'name': 'layer'+idx+'4'}},
            {'name': 'Linear',  'params': {'input_dim': 2, 'output_dim': 1, 'name': 'layer'+idx+'5'}}],
        sm=[]
    )[args.kern]
    return kernel, wrapper

def load_texture(img_name, h_min=60, h_max=120, w_min=130, w_max=210):
    def rgb2gray(rgb):
        return np.dot(rgb[..., :3], [0.299, 0.587, 0.114])
    rgb = mpimg.imread(os.path.join(DATA_PATH, img_name+'.png'))
    gray = rgb2gray(rgb)

    nx1, nx2 = gray.shape
    x_train1 = np.arange(nx1) / nx1
    x_train2 = np.arange(nx2) / nx2
    y_train = copy.copy(gray)
    y_train[h_min:h_max, w_min:w_max] = np.random.randn(h_max - h_min, w_max - w_min) * 1e3
    x_test1 = np.arange(h_min, h_max) / nx1
    x_test2 = np.arange(w_min, w_max) / nx2
    y_test = gray[h_min:h_max, w_min:w_max]
    gt = copy.copy(gray)
    mask = np.zeros_like(gray, dtype=np.int32)
    mask[h_min:h_max, w_min:w_max] = 1
    hparams = HParams(
        x_train1=np.expand_dims(x_train1, 1),
        x_train2=np.expand_dims(x_train2, 1),
        y_train=y_train,
        x_test1=np.expand_dims(x_test1, 1),
        x_test2=np.expand_dims(x_test2, 1),
        y_test=y_test,
        gt=gt,
        mask=mask,
    )
    return hparams

############################## training ##############################
fig_size = 224
divide = 4
predict_fig = np.zeros((fig_size, fig_size))

for h in range(divide):
    for w in range(divide):
        print("\nh:",h+1,"/", divide, ",","w:",w+1,"/", divide)
        ############################## load data ##############################
        data = load_texture(args.data, h*int(fig_size/divide), (h+1)*int(fig_size/divide), w*int(fig_size/divide), (w+1)*int(fig_size/divide))
        x_train1, x_train2 = data.x_train1.astype(FLOAT_TYPE), data.x_train2.astype(FLOAT_TYPE)
        y_train = data.y_train.astype(FLOAT_TYPE)
        x_test1, x_test2 = data.x_test1.astype(FLOAT_TYPE), data.x_test2.astype(FLOAT_TYPE)
        y_test = data.y_test.astype(FLOAT_TYPE)

        mask = data.mask.astype(FLOAT_TYPE)
        res = copy.copy(y_train)

        ############################## build graph ##############################
        kernel1, wrapper1 = NKNInfo(x_train1, str(h*divide+w))
        kernel1 = NeuralKernelNetwork(1, KernelWrapper(kernel1), NKNWrapper(wrapper1))

        kernel2, wrapper2 = NKNInfo(x_train2, str(h*divide+w+100))
        kernel2 = NeuralKernelNetwork(1, KernelWrapper(kernel2), NKNWrapper(wrapper2))

        model = gfs.models.KGPR(x_train1, x_train2, y_train, kernel1, kernel2, mask, name=str(h*divide+w))

        loss = model.objective
        optimizer = tf.train.AdamOptimizer(1e-3, name=str(h*divide+w))

        infer = optimizer.minimize(loss)
        pred_mu = model.predict_f(x_test1, x_test2)
        obs_var = model.likelihood.variance

        ############################## session run ##############################
        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())
            for epoch in range(1501):
                _, obj = sess.run([infer, loss])

                if epoch % 500 == 0:
                    var = sess.run(obs_var)
                    print('Epoch {} | loss = {:.4f} | var: {:.4f}'.format(epoch, obj, var))

                """if epoch % 500 == 0:
                    mu = sess.run(pred_mu)
                    res[60:120, 130:210] = mu
                    path = osp.join('results/texture/'+args.data, args.kern, 'epoch_{}.png'.format(epoch))
                    makedirs(path)
                    mpimg.imsave(path, res, cmap=plt.get_cmap('gray'))"""
            mu = sess.run(pred_mu)
            predict_fig[h*int(fig_size/divide):(h+1)*int(fig_size/divide), w*int(fig_size/divide):(w+1)*int(fig_size/divide)] = mu
            
path = osp.join('results/texture/'+args.data, args.kern, 'result.png')
makedirs(path)
mpimg.imsave(path, predict_fig, cmap=plt.get_cmap('gray'))
