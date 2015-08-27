# -*- coding: utf-8 -*-


import json
from path import Path
import sys
from multiprocessing import Pool
import re
import argparse
from itertools import repeat
import time
import multiprocessing
import random
import numpy as np
from scipy import io
from scipy.sparse import coo_matrix
import cPickle as pickle
import random

LINE_PER_CORE = 1000
NUM_CORE = multiprocessing.cpu_count()-1
# NUM_CORE = 1

def save_sparse_csr(file_name,array):
    np.savez(file_name,data = array.data ,col=array.col,
             row =array.row, shape=array.shape )


def load_sparse_csr(file_name):
    loader = np.load(file_name)
    return coo_matrix((loader['data'], (loader['row'], loader['col'])),shape = loader['shape'])


def build_matrix(file_name):
    print "Building matrix..."
    _dict = {}
    pro_id = []
    user_id = []
    rating = []
    with open(file_name, 'r') as f_in:
        for l in f_in:
            tokens = l.strip().split('\t')
            k = tokens[0] + "_" + tokens[1]
            _dict[k] = l.strip()
            pro_id.append(int(tokens[0]) - 1)
            user_id.append(int(tokens[1]) - 1)
            rating.append(int(float(tokens[2])))
    pro_id = np.array(pro_id)
    user_id = np.array(user_id)
    rating = np.array(rating)
    _matrix = coo_matrix((rating, (pro_id, user_id)), shape=(np.max(pro_id) + 1, np.max(user_id) + 1))
    print "Finished building"
    return _matrix, _dict


def random_one(_matrix, pro_id, user_id, rating, is_same_rating=True):
    def random_func(array):
        if is_same_rating:
            b = 0
            while True:
                index = []
                for i, j in zip(array.indices, array.data):
                    if j == rating + b or j == rating - b:
                        index.append(i)
                if index:
                    # print "index", index
                    return random.choice(index)
                b += 1
        else:
            return random.choice(array.indices)

    pro_id = int(pro_id) - 1
    user_id = int(user_id) - 1
    rating = int(float(rating))
    same_pro = _matrix.getrow(pro_id)
    same_user = _matrix.getcol(user_id).tocsc()
    return (pro_id, random_func(same_pro)), (random_func(same_user), user_id)


def process_one((_in, _matrix)):
    r_list = []
    for l in _in:
        l = l.strip()
        tokens = l.split('\t')
        pro_id = tokens[0]
        user_id = tokens[1]
        rating = tokens[2]
        p, u = random_one(_matrix, pro_id, user_id, rating)
        r_list.append((l, p, u))
    return r_list


def do(l_list,f_out_1, f_out_2, _matrix, _dict):
    pool = Pool(NUM_CORE)
    r_list=pool.map(process_one,zip([l_list[it:it+LINE_PER_CORE] for it in xrange(0,len(l_list),LINE_PER_CORE)], repeat(_matrix)))
    # print len(l_list)
    # r_list = process_one((l_list, _matrix))
    pool.close()
    pool.join()

    for r in r_list:
        for j in r:
            l, p, u = j
            print >>f_out_1, l
            print >>f_out_1, _dict[str(p[0]+1) + "_" + str(p[1]+1)]
            print >>f_out_2, l
            print >>f_out_2, _dict[str(u[0]+1) + "_" + str(u[1]+1)]

if __name__ == "__main__":
    file_name = '../data/train_dump.txt'
    _matrix, _dict = build_matrix(file_name)
    test_file = "../data/test.txt"
    with open('../data/same_pro_rand.txt','w') as f_out_1:
        with open('../data/same_user_rand.txt', 'w') as f_out_2:
            l_list=[]
            g = open(test_file, 'r')
            for l in g:
                if len(l_list)<NUM_CORE*LINE_PER_CORE:
                    l_list.append(l)
                else:
                    print "starting", time.strftime('%Y-%m-%d %X', time.localtime())
                    do(l_list, f_out_1, f_out_2, _matrix, _dict)
                    l_list=[]
                    print time.strftime('%Y-%m-%d %X', time.localtime())
            if len(l_list)>0:
                do(l_list, f_out_1, f_out_2, _matrix, _dict)