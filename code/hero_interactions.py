import pandas as pd
import cPickle as pickle
import numpy as np
from collections import defaultdict
from scipy import stats
import sys


class HeroWinratePickler(object):
    '''pickles hero winrates, hero pair winrates, and hero head-to-head winrates'''
    def __init__(self, data_folder_path, last_patch_num):
        self.data_folder_path = data_folder_path
        self.last_patch_num = int(last_patch_num)
        self.hero_wrs = None

    def make_wr_pickle(self, pickle_name='hero_winrates'):
        hero_wrs = {}
        for i in xrange(677, self.last_patch_num+1):
            df = pd.read_csv('{0}/hero_stats/heroes_{1}.csv'.format(self.data_folder_path, i))
            df.loc[df[df['Hero']=='furion'].index[0], 'Name'] = "Nature's Prophet" # fix apostrophe
            df.loc[df[df['Hero']=='antimage'].index[0], 'Name'] = "Anti-Mage" # fix hyphen
            hero_wrs[i] = df[['Name', 'W', 'L', 'Win %']].set_index('Name')

        self.hero_wrs = hero_wrs # reserved for other methods to access
        with open('{0}/{1}.pkl'.format(self.data_folder_path, pickle_name), 'w') as f:
            pickle.dump(hero_wrs, f)

    def check_sig(self, hero, patch_num, pair_wins, pair_losses, threshold=0.1):
        hero_wr_df = self.hero_wrs[patch_num]
        solo_wins = hero_wr_df.loc[hero]['W']
        solo_losses = hero_wr_df.loc[hero]['L']
        contingency_table = np.array([[pair_wins, pair_losses], [solo_wins, solo_losses]])
        return stats.chi2_contingency(contingency_table)[1] < threshold


    def one_patch_interactions(self, pair_type, patch_num, interaction_df):
        patch_hero_wrs = self.hero_wrs[patch_num]
        hero_interactions = defaultdict(list)
        for _, pair in interaction_df.iterrows():
            hero, other, pair_wr = pair['Name'], pair['Name.1'], pair['Win %']
            hero = hero.replace('Natures Prophet', "Nature's Prophet").replace('Anti Mage', 'Anti-Mage')
            other = other.replace('Natures Prophet', "Nature's Prophet").replace('Anti Mage', 'Anti-Mage')
            hero_solo_wr = patch_hero_wrs.loc[hero]['Win %']
            other_solo_wr = patch_hero_wrs.loc[other]['Win %']

            if pair_type == 'pair':
                hero_sig = self.check_sig(hero, patch_num, pair['W'], pair['L'])
                other_sig = self.check_sig(other, patch_num, pair['W'], pair['L'])
                hero_interactions[hero].append((other, round(pair_wr - hero_solo_wr, 4), hero_sig))
                hero_interactions[other].append((hero, round(pair_wr - other_solo_wr, 4), other_sig))

            else:
                hero_sig = self.check_sig(hero, patch_num, pair['W'], pair['L'])
                other_sig = self.check_sig(other, patch_num, pair['L'], pair['W'])
                hero_interactions[hero].append((other, round(pair_wr - hero_solo_wr, 4), hero_sig))
                hero_interactions[other].append((hero, round((1 - pair_wr) - other_solo_wr, 4), other_sig))

        return hero_interactions

    def make_pairs_pickle(self, pair_type, pickle_name):
        if pair_type not in ['pair', 'counter']:
            print 'argument pair_type must be either \'pair\' or \'counter\''
            return

        hero_pairs_by_patch = {}
        for i in xrange(677, self.last_patch_num+1):
            df = pd.read_csv('{0}/{1}_stats/{1}s_{2}.csv'\
                   .format(self.data_folder_path, pair_type, i))
            hero_pairs_by_patch[i] = df

        all_patch_interaction_dicts = {}
        for i in xrange(677, self.last_patch_num+1):
            interaction_df = hero_pairs_by_patch[i]
            hero_interactions_dict = self.one_patch_interactions(pair_type, i, interaction_df)
            all_patch_interaction_dicts[i] = hero_interactions_dict

        with open('{0}/{1}.pkl'.format(self.data_folder_path, pickle_name), 'w') as f:
            pickle.dump(all_patch_interaction_dicts, f)

if __name__ == '__main__':
    data_folder_path = sys.argv[1]
    last_patch_num = sys.argv[2]
    winrate_pickler = HeroWinratePickler(data_folder_path, last_patch_num)
    winrate_pickler.make_wr_pickle('hero_winrates')
    winrate_pickler.make_pairs_pickle('pair', 'hero_ally_pairs')
    winrate_pickler.make_pairs_pickle('counter', 'hero_counter_pairs')
