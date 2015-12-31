import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import cPickle as pickle
import json

def get_hero_names():
    '''
    helper function for df_from_patch_query;
    scrapes dota2 official site for set of hero names.
    '''
    r_heroes = requests.get('http://www.dota2.com/heroes/')
    soup_heroes = BeautifulSoup(r_heroes.content, 'html.parser')
    hero_name_set = set()
    for column in soup_heroes.findAll('div', {'class': 'heroIcons'}):
        for a_tag in column.findAll('a'):
            hero_name_set.add(a_tag['href'].split('/')[-2].replace('_', ' '))

    hero_name_set.remove('Natures Prophet')
    hero_name_set.add("Nature's Prophet") # dota2.com doesn't include apostrophe

    return hero_name_set

def get_abi_names(filepath):
    '''
    builds set of ability names to use as stopwords in remove_abi_names.
    '''
    with open(filepath) as f:
        abi_json = json.load(f)
    ability_set = set(ability['localizedName'] for ability in abi_json)
    ability_set.remove('') # discard empty string
    return ability_set

def build_df(hero_change_dict, hero_name_set, patch_name):
    '''
    helper function; creates DataFrame to return in df_from_patch_query
    '''
    heroes = []
    change_text = []
    for hero, text_list in hero_change_dict.iteritems():
        heroes.append(hero)
        change_text.append(text_list)

    df = pd.DataFrame({'hero': heroes, 'text': change_text, 'patch': [patch_name]*len(heroes)})
    changed_heroes_685 = set(df.hero.values)
    untouched_heroes = []
    for hero in hero_name_set:
        if not hero in changed_heroes_685:
            untouched_heroes.append(hero)

    df_all_heroes = pd.concat([df, pd.DataFrame({'hero': untouched_heroes,
                                                 'text': [[]]*len(untouched_heroes),
                                                 'patch': [patch_name]*len(untouched_heroes)})])
    df_all_heroes.sort('hero', inplace=True)
    df_all_heroes.reset_index(inplace=True)
    df_all_heroes.drop('index', axis=1, inplace=True)

    return df_all_heroes

def df_from_patch_query(page, hero_name_set, patch_name):
    '''
    INPUT: patch page url as string, set of acceptable hero names, patch label as string
    OUTPUT: dataframe of hero | list of change texts | patch label ('6.84' etc.)

    The html tag search here is admittedly idiosyncratic but appears to perform
    as desired for all patch pages.
    '''
    r = requests.get('https://dota2.gamepedia.com/{0}'.format(page))
    soup = BeautifulSoup(r.content, 'html.parser')

    hero_change_dict = defaultdict(list)
    for ul in soup.find('div', {'id': 'mw-content-text'}).find('div', recursive=False).findAll('ul', recursive=False):
        try:
            li = ul.find('li')
            if li.find('a')['title'] in hero_name_set:
                for sub_ul in li.findAll('ul', recursive=False):
                    for sub_li in sub_ul.findAll('li', recursive=False):
                        hero_change_dict[li.find('a')['title']].append(sub_li.text.strip())
        except:
            continue

    df = build_df(hero_change_dict, hero_name_set, patch_name)
    return df

def remove_abi_names(changelist, abi_set=None):
    '''
    INPUT: one hero's list of changes, set of recognized ability names
    OUTPUT: hero's changelist with ability names removed
    '''
    changes_trimmed = []
    for i, item in enumerate(changelist):
        changes_trimmed.append(item)
        for abi in abi_set:
            item = item.replace(abi, '').strip()
            changes_trimmed[i] = item
    return changes_trimmed
