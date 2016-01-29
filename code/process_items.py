import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import cPickle as pickle
import dota2api
from make_patch_df import get_hero_names


def get_item_names():
    d2a = dota2api.Initialise()
    all_items = set(item['localized_name'] for item in d2a.get_game_items()['items'] if item['id'] < 1000)
    recipes = set(item['localized_name'] for item in d2a.get_game_items()['items'] if item['localized_name'].startswith('Recipe:'))
    return all_items.difference(recipes)


def get_hero_items():
    hero_items_dict = {}
    hero_name_set = get_hero_names()
    item_name_set = get_item_names()
    for hero_name in hero_name_set:
        hero_url_ending = '_'.join(hero_name.split(' '))
        r = requests.get('https://dota2.gamepedia.com/{0}'.format(hero_url_ending))
        soup = BeautifulSoup(r.content, 'html.parser')
        hero_items_raw = [a['title'] for a in soup.find('table', class_='navbox').findAll('a')[3:]]
        hero_items = set(item.split('(')[0].strip() for item in hero_items_raw)
        hero_items_dict[hero_name] = hero_items
    return hero_items_dict
