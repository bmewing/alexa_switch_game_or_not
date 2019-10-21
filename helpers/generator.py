#!/usr/bin/python3

import json
import random
import re
from fuzzywuzzy import fuzz
from functools import reduce


def choose_letter(s):
    r = random.random()
    p = probs[s]
    i = min([i for i, x in enumerate([r < l for l in list(p.values())]) if x])
    return list(p.keys())[i]


def gen_title(title, n):
    keep_going = True
    while keep_going:
        if title[-n:] == "`" * n:
            keep_going = False
        else:
            title = title + choose_letter(title[-n:])
    return title[n:-n]


def check_name(name, known, generated):
    result = False
    if len(name) > 30:
        result = True
    if name in known:
        result = True
    if any([True for k in known if re.search(name, k)]):
        result = True
    if name in generated:
        result = True
    if any([fuzz.partial_ratio(name.lower(), k.lower()) == 90 for k in known]):
        result = True
    if any([fuzz.partial_ratio(k.lower(), name.lower()) == 90 for k in known]):
        result = True
    if any([fuzz.partial_ratio(name.lower(), k.lower()) >= 60 for k in generated]):
        result = True
    if re.findall(":+", name).__len__() > 1 or re.findall("\?+", name).__len__() > 1:
        result = True
    if re.findall("-$", name).__len__() == 1:
        result = True
    return result


def fetch_games():
    with open('fake_games.txt', 'r') as f:
        fakes = f.readlines()
    with open('real_games.txt', 'r') as f:
        reals = f.readlines()
    return reals, fakes


if __name__ == "__main__":
    known_games, fake_game_list = fetch_games()

    memory_length = 4

    with open('helpers/markov_probabilities_{}.json'.format(str(memory_length))) as jf:
        probs = json.load(jf)

    start = '*' * memory_length
    new_fake_games = 0
    with open('fake_games.txt', 'a') as f:
        while new_fake_games < 10:
            out = gen_title(start, memory_length)
            if not check_name(out, known_games, fake_game_list):
                fake_game_list.append(out)
                new_fake_games += 1
                f.write(out+'\n')
                print(out)
