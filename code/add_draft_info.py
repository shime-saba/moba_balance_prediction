import pandas as pd
import numpy as np
from patch_nlp import get_info_from_df
from make_patch_df import df_from_patch_query

def get_draft_dfs(folder_path, last_patch=686):
    all_draft_dfs = {}
    for i in xrange(677, last_patch+1):
        df = pd.read_csv('{0}/drafts_{1}.csv'.format(folder_path, i))
        df.loc[df[df['Hero']=='furion'].index[0], 'Name'] = "Nature's Prophet" # fix apostrophe
        df.drop(['Hero', 'Times Picked', 'Times Banned'], axis=1, inplace=True)
        df.columns = ['hero', 'pick%', 'ban%', 'pb%', 'times_pb']
        all_draft_dfs[i] = df.copy()

    return all_draft_dfs

def prepare_draft_dfs(drafts_dict):
    for patch_num, df in drafts_dict.iteritems():
        if patch_num > min(drafts_dict.keys()):
            prev_df = drafts_dict[patch_num-1]
            prev_pbs = dict(prev_df[['hero', 'pb%']].values)
            old_pb_list = []
            for hero in df['hero']:
                if hero in prev_pbs:
                    old_pb_list.append(prev_pbs[hero])
                else:
                    old_pb_list.append(None)
            df['prev_patch_pb%'] = old_pb_list
        else:
            df['prev_patch_pb%'] = [None]*len(df)

        df['patch'] = [patch_num]*len(df)

    return drafts_dict


def get_patch_dfs(patch_url_dict, hero_name_set, ability_set, tfidf_train, model):
    all_patches = {}
    for patch_num, url in patch_url_dict.iteritems():
        if not patch_num == '6.85':
            df = df_from_patch_query(url, hero_name_set, ability_set, patch_num)
            texts, ratios = get_info_from_df(df, labeled=False)

            tfmat_test = tfidf_train.transform(texts)
            model_output = np.round(model.predict_proba(tfmat_test.toarray())[:,1], 4)

            counter = 0
            predictions = []
            ratios_by_hero = []
            for item in df['text']:
                predictions.append(model_output[counter:counter+len(item)])
                ratios_by_hero.append(ratios[counter:counter+len(item)])
                counter += len(item)
            df['predictions'] = predictions
            df['ratios'] = ratios_by_hero

            all_patches[patch_num] = df

    return all_patches
