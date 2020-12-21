# -*- coding: utf-8 -*-
import json
import re

_start_hero_pattern = '\t"npc_dota_hero_'
_start_item_pattern = '\t"item_'
_start_ability_pattern = '\t"'

import pathlib

from io import StringIO


def open_or_stringIO(f, as_string=False):
    """
    Useful for testing, but not sure how good it actually is.
    """
    try:
        p = pathlib.Path(f)
        if p.exists() and not as_string:
            return open(f)
        else:
            return StringIO(f)
    except OSError:
        return StringIO(f)


def parse_abilities(ability_file):
    with open_or_stringIO(ability_file) as f:
        blocks = []
        for line in f:
            if (line.startswith(_start_ability_pattern) and
                    not line.startswith('\t"Version"')):
                block = get_ability_block(f, line)
                blocks.append(block)

    ability_d = _construct_json(blocks)

    with open("abilities_parsed.json", 'w') as f:
        json.dump(ability_d, f)
        print("Parsed Abilities.")


def parse_heroes(hero_file='../npc_heroes.txt'):
    with open_or_stringIO(hero_file) as f:
        hero_blocks = []
        for line in f:
            if line.startswith(_start_hero_pattern):
                hero_block = get_hero_block(f, line)
                hero_blocks.append(hero_block)

    hero_d = _construct_json(hero_blocks)

    with open("heroes_parsed.json", 'w') as f:
        json.dump(hero_d, f)
        print("Parsed Heros.")


def _construct_json(blocks):
    d = {}
    for block in blocks:
        d[block[0][1].lower()] = {k.lower(): v for k, v in block[1:]}

    return d


def get_hero_block(f, line):
    results = get_block(f, line, kind='hero')
    return results  # results isn't unique cause nesting


def get_hero_names(heros):
    ids = {}
    for hero in heros:
        d = dict(hero)
        name = d['name']
        hero_id = d.get('HeroID', 0)
        ids[int(hero_id)] = name
    return ids


def get_ability_block(f, line):
    results = get_block(f, line, kind='ability')
    return results


def get_block(f, line, kind):
    if kind == 'hero':
        name = line.split(_start_hero_pattern)[1].rstrip('"\t\n')
    elif kind == 'ability':
        name = line.strip().strip('"')
    elif kind == 'item':
        name = line.split(_start_item_pattern)[1].rstrip('"\t\n')

    f.readline()  # {
    n_open = 1

    pair = re.compile(r'\t*\"(.+)\"\s*\"(.+)\"')

    results = []
    results.append(('name', name))
    for line in f:
        if re.search(r'\t+{', line):
            n_open += 1
        elif re.search(r'\t+}', line):
            n_open -= 1
            if n_open == 0:
                break
        elif re.search(pair, line):
            results.append(re.search(pair, line).groups())

    return results


parse_abilities('data/npc_abilities.txt')
