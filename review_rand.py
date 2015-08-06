# -*- coding: utf-8 -*-


import sqlite3
import random
import bleu


def build_db(file_name):
    cx = sqlite3.connect(file_name + ".db")
    cu = cx.cursor()
    table = "data"
    cu.execute("drop table " + table)
    cu.execute("create table data (pro_id integer, user_id integer, rating integer, review varchar(1000))")
    with open(file_name, "r") as f_in:
        for l in f_in:
            tokens = l.strip().split("\t")
            value = "values(%s, %s, %s, '%s')" % (tokens[0], tokens[1], tokens[2], tokens[3])
            cu.execute("insert into data " + value)
    cx.commit()

def load_model(db_file_name):
    cx = sqlite3.connect(db_file_name)
    return cx

def get_cases(cx, pro_id=None, user_id=None, rating=None, num=None):
    cu = cx.cursor()
    table = "data"
    query = "SELECT * FROM %s" % table
    cons = []
    if pro_id:
        cons.append("pro_id=%s" % pro_id)
    if user_id:
        cons.append("user_id=%s" % user_id)
    if rating:
        cons.append("rating=%s" % rating)
    if cons:
        query += " WHERE " + " AND ".join(cons)
    cu.execute(query)
    cols = cu.fetchall()
    result = [t[-1] for t in cols]
    if num:
        return random.sample(result, num)
    return result

if __name__ == "__main__":
    for f in Path(input_folder).files('*.txt'):
        build_db(f.abspath())

    # test = "the the the the the the the"
    #
    # file_name = "train"
    # build_db(file_name)
    # cx = load_model(file_name + '.db')
    # refs = get_cases(cx, user_id=1)
    # print(bleu.score_all([test], [refs], 3))