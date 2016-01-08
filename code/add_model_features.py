import pandas as pd
import numpy as np

def add_pair_features(df):
    df = df.copy()
    composite_ally_change = np.zeros(len(df))
    composite_counter_change = np.zeros(len(df))
    for i, row in df.iterrows():
        allies = row['prev_patch_allies']
        counters = row['prev_patch_counters']
        for ally in allies:
            ally_pred = df[df['hero']==ally[0]]['avg_pred'].values[0]
            if ally[1] > 0 and not np.isnan(ally_pred):
                composite_ally_change[i] += ally[1] * ally_pred
        for counter in counters:
            counter_pred = df[df['hero']==counter[0]]['avg_pred'].values[0]
            if not np.isnan(counter_pred):
                composite_counter_change[i] += counter[1] * counter_pred

    df['composite_ally_change'] = composite_ally_change
    df['composite_counter_change'] = composite_counter_change
    return df

def count_pred_values(df):
    df = df.copy()
    num_changes_0_4 = np.zeros(len(df))
    num_changes_4_6 = np.zeros(len(df))
    num_changes_6_7 = np.zeros(len(df))
    num_changes_7_8 = np.zeros(len(df))
    num_changes_8_9 = np.zeros(len(df))
    num_changes_9_10 = np.zeros(len(df))
    for i, pred_list in enumerate(df['predictions']):
        for item in pred_list:
            if 0 <= item < 0.4:
                num_changes_0_4[i] += 1
            elif 0.4 <= item < 0.6:
                num_changes_4_6[i] += 1
            elif 0.6 <= item < 0.7:
                num_changes_6_7[i] += 1
            elif 0.7 <= item < 0.8:
                num_changes_7_8[i] += 1
            elif 0.8 <= item < 0.9:
                num_changes_8_9[i] += 1
            elif item >= 0.9:
                num_changes_9_10[i] += 1
            else:
                print pred_list
    df['num_changes_0_4'] = num_changes_0_4
    df['num_changes_4_6'] = num_changes_4_6
    df['num_changes_6_7'] = num_changes_6_7
    df['num_changes_7_8'] = num_changes_7_8
    df['num_changes_8_9'] = num_changes_8_9
    df['num_changes_9_10'] = num_changes_9_10

    return df


def add_features(df):
    df = df.copy()
    df['avg_pred'] = df['predictions'].apply(np.mean)
    df['num_changes'] = df['predictions'].apply(np.size)
    num_numeric_changes = []
    for i, row in df.iterrows():
        num_numeric_changes.append(np.sum(np.array(row['ratios']) >= 0))
    df['num_numeric_changes'] = num_numeric_changes
    avg_ratio = []
    for ratio_list in df['ratios']:
        ratios = np.array(ratio_list)
        mean_ratio = np.mean(ratios[ratios >= 0])
        if type(mean_ratio) in [float, np.float64] and not np.isnan(mean_ratio):
            avg_ratio.append(np.mean(ratios[ratios >= 0]))
        else:
            avg_ratio.append(1)
    df['avg_ratio'] = avg_ratio
    df = count_pred_values(df)
    pred_dummies = pd.get_dummies(pd.cut(df['avg_pred'], [0, 0.4, 0.6, 0.7, 0.8, 0.9, 1.01]), prefix='avg_pred', dummy_na=True)
    df = pd.concat([df, pred_dummies], axis=1)
    df = add_pair_features(df)
    return df
