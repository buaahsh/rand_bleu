#!/usr/bin/python
# -*- coding: utf-8 -*-
# File originally part of moses package: http://www.statmt.org/moses/ (as bleu.py)
# Stripped of unused code to reduce number of libraries used

# $Id$

"""
Provides:

cook_refs(refs, n=4): Transform a list of reference sentences as strings into a form usable by cook_test().
cook_test(test, refs, n=4): Transform a test sentence as a string (together with the cooked reference sentences) into
a form usable by score_cooked().
score_cooked(alltest, n=4): Score a list of cooked test sentences.

The reason for breaking the BLEU computation into three phases cook_refs(), cook_test(), and score_cooked() is to
allow the caller to calculate BLEU scores for multiple test sets as efficiently as possible.
"""

from __future__ import division
import math
import re
import xml.sax.saxutils
import time

# Added to bypass NIST-style pre-processing of hyp and ref files -- wade
nonorm = False

preserve_case = False
eff_ref_len = "shortest"

normalize1 = [
    ('<skipped>', ''),         # strip "skipped" tags
    (r'-\n', ''),              # strip end-of-line hyphenation and join lines
    (r'\n', ' '),              # join lines
   # (r'(\d)\s+(?=\d)', r'\1'), #  join digits
]
normalize1 = [(re.compile(pattern), replace) for (pattern, replace) in normalize1]

normalize2 = [
    (r'([\{-\~\[-\` -\&\(-\+\:-\@\/])',r' \1 '), # tokenize punctuation. apostrophe is missing
    (r'([^0-9])([\.,])',r'\1 \2 '),              # tokenize period and comma unless preceded by a digit
    (r'([\.,])([^0-9])',r' \1 \2'),              # tokenize period and comma unless followed by a digit
    (r'([0-9])(-)',r'\1 \2 ')                    # tokenize dash when preceded by a digit
]
normalize2 = [(re.compile(pattern), replace) for (pattern, replace) in normalize2]

#combine normalize2 into a single regex.
normalize3 = re.compile(r'([\{-\~\[-\` -\&\(-\+\:-\@\/])|(?:(?<![0-9])([\.,]))|(?:([\.,])(?![0-9]))|(?:(?<=[0-9])(-))')

def normalize(s):
    """
    :param s:
    :return:
    Normalize and tokenize text. This is lifted from NIST mteval-v11a.pl.
    """
    # Added to bypass NIST-style pre-processing of hyp and ref files -- wade
    if nonorm:
        return s.split()
    try:
        s.split()
    except:
        s = " ".join(s)
    # language-independent part:
    for (pattern, replace) in normalize1:
        s = re.sub(pattern, replace, s)
    s = xml.sax.saxutils.unescape(s, {'&quot;':'"'})
    # language-dependent part (assuming Western languages):
    s = " %s " % s
    if not preserve_case:
        s = s.lower()         # this might not be identical to the original
    return [tok for tok in normalize3.split(s) if tok and tok != ' ']

def count_ngrams(words, n=4):
    counts = {}
    for k in range(1,n+1):
        for i in range(len(words)-k+1):
            ngram = tuple(words[i:i+k])
            counts[ngram] = counts.get(ngram, 0)+1
    return counts

def cook_refs(refs, n=4):
    """
    Takes a list of reference sentences for a single segment
    and returns an object that encapsulates everything that BLEU
    needs to know about them.
    """
    
    refs = [normalize(ref) for ref in refs]
    maxcounts = {}
    for ref in refs:
        counts = count_ngrams(ref, n)
        for (ngram,count) in counts.items():
            maxcounts[ngram] = max(maxcounts.get(ngram,0), count)
    return ([len(ref) for ref in refs], maxcounts)

def cook_test(test, args, n=4):
    '''Takes a test sentence and returns an object that
    encapsulates everything that BLEU needs to know about it.'''
    
    reflens, refmaxcounts = args
    test = normalize(test)
    result = {}
    result["testlen"] = len(test)

    # Calculate effective reference sentence length.
    
    if eff_ref_len == "shortest":
        result["reflen"] = min(reflens)
    elif eff_ref_len == "average":
        result["reflen"] = float(sum(reflens))/len(reflens)
    elif eff_ref_len == "closest":
        min_diff = None
        for reflen in reflens:
            if min_diff is None or abs(reflen-len(test)) < min_diff:
                min_diff = abs(reflen-len(test))
                result['reflen'] = reflen

    result["guess"] = [max(len(test)-k+1,0) for k in range(1,n+1)]

    result['correct'] = [0]*n
    counts = count_ngrams(test, n)
    for (ngram, count) in counts.items():
        result["correct"][len(ngram)-1] += min(refmaxcounts.get(ngram,0), count)

    return result

def score_cooked(all_comps, n=4, is_smooth=True):
    total_comps = {'testlen':0, 'reflen':0, 'guess':[0]*n, 'correct':[0]*n}
    for comps in all_comps:
        for key in ['testlen','reflen']:
            total_comps[key] += comps[key]
        for key in ['guess','correct']:
            for k in range(n):
                total_comps[key][k] += comps[key][k]
    logbleu = 0.0
    invcnt = 1
    for k in range(n):
        if k !=0 :
            total_comps['correct'][k] += 1
            total_comps['guess'][k] += 1
        # if total_comps['correct'][k] == 0:
        #     if not is_smooth:
        #         return 0.0
        #     invcnt *= 2
        #     total_comps['correct'][k] = 1.0 / invcnt
        logbleu += math.log(total_comps['correct'][k])-math.log(total_comps['guess'][k])
    logbleu /= float(n)
    logbleu += min(0,1-float(total_comps['reflen'])/total_comps['testlen'])
    return math.exp(logbleu)

def score_all(test, refs, n=2, is_smooth=True):
    cooked_test = []
    index = -1
    for t, r in zip(test, refs):
        index += 1
        if index % 10000 == 0:
            print index, time.strftime('%Y-%m-%d %X', time.localtime())
        ct = cook_test(t, cook_refs(r, n), n)
        cooked_test.append(ct)
    score = score_cooked(cooked_test, n)
    return score

if __name__ == "__main__":
    file_name = "same_user_rand.txt"
    file_name = "same_pro_rand.txt"
    file_name = "save_epoch16.17_2.4484.t7.sample"
    with open(file_name, 'r') as f_in:
        r = 0
        test = []
        refs = []
        
        for l in f_in:
            
            if r == 0:
                test.append(l.strip())
                r = 1
            else:
                refs.append([l.strip()])
                r = 0
    n = 4
    print(score_all(test,refs, n))