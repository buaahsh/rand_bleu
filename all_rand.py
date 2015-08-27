# -*- coding: utf-8 -*-


from multiprocessing import Pool
from itertools import repeat
import time
import multiprocessing
import random

LINE_PER_CORE = 1000
NUM_CORE = multiprocessing.cpu_count()-1


def build_matrix(file_name):
    reviews = []
    with open(file_name, 'r') as f_in:
        for l in f_in:
            tokens = l.strip().split('\t')
            reviews.append(l.strip())
    return reviews


def process_one((_in, reviews)):
    r_list = []
    for l in _in:
        l = l.strip()
        index = random.randint(0, len(reviews))
        r = reviews[index]
        r_list.append((l, r))
    return r_list


def do(l_list,f_out_1, reviews):
    # pool = Pool(NUM_CORE)
    # r_list=pool.map(process_one,zip([l_list[it:it+LINE_PER_CORE] for it in xrange(0,len(l_list),LINE_PER_CORE)], repeat(reviews)))
    # pool.close()
    # pool.join()

    for r in l_list:
        l = r.strip()
        index = random.randint(0, len(reviews) - 1)
        r = reviews[index]
        print >>f_out_1, l
        print >>f_out_1, r.strip()

if __name__ == "__main__":
    file_name = '../data/train_dump.txt'
    reviews = build_matrix(file_name)
    test_file = "../data/test.txt"
    output_file = "../data/all_rand.txt"
    with open(output_file, 'w') as f_out_1:
        l_list=[]
        g = open(test_file, 'r')
        for l in g:
            if len(l_list)<NUM_CORE*LINE_PER_CORE:
                l_list.append(l)
            else:
                do(l_list, f_out_1, reviews)
                l_list=[]
                print time.strftime('%Y-%m-%d %X', time.localtime())
        if len(l_list)>0:
            do(l_list, f_out_1, reviews)
