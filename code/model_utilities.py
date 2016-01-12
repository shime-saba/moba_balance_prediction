import cPickle as pickle
import pandas as pd
import numpy as np
from add_model_features import add_features
import matplotlib.pyplot as plt


def get_all_dfs(data_folder_path):
    '''
    INPUT: path to data folder
    OUTPUT: dictionary of dataframes of patch/drafting info
            (extra features from add_model_features have not been added)
    '''
    with open('{0}/all_patch_draft_dfs.pkl'.format(data_folder_path)) as f:
        patch_draft_dfs = pickle.load(f)
    del patch_draft_dfs['6.77']  # first patch recorded; no "prev. patch" data
    for key, df in patch_draft_dfs.iteritems():
        df = df.copy()
        patch_draft_dfs[key] = add_features(df)
    return patch_draft_dfs


def get_X_and_y(df, model_type, threshold=60):
    '''
    INPUT: dataframe, type of model (regressor or classifier), threshold for
           use in classification problem
    OUTPUT: X (modeling variables) and y (target/response variable) arrays
    '''
    df = df.copy()
    df.drop(['hero',
             'patch',
             'text',
             'text_no_abi',
             'predictions',
             'ratios',
             'pick%',
             'ban%',
             'times_pb',
             'prev_patch_allies',
             'prev_patch_counters',
             'avg_pred'], axis=1, inplace=True)
    df['prev_patch_pb%'] = df['prev_patch_pb%'].fillna(0)
    df['prev_patch_winrate'] = df['prev_patch_winrate'].fillna(0)
    if model_type == 'classifier':
        df['over60'] = df['pb%'].apply(lambda x: 1 if x > threshold else 0)
        df.drop('pb%', axis=1, inplace=True)
        y = df.pop('over60').values
        X = df.values
    elif model_type == 'regressor':
        y = df.pop('pb%').values
        X = df.values
    else:
        print "Type must be regressor or classifier"
        return 0, 0

    return X, y


def one_patch_predictor(patch_draft_dfs, target_patch, model, model_type, threshold=60):
    '''
    OUTPUT: true y values, previous patch values, model predictions
    (if model_type is 'classifier', predictions are prob. of pb% > 60)
    '''
    patch_draft_dfs = patch_draft_dfs.copy()
    df_target = patch_draft_dfs.pop(target_patch)
    df_no_target = pd.concat(patch_draft_dfs, keys=None)

    X_train, y_train = get_X_and_y(df_no_target, model_type, threshold)
    X_test, y_test = get_X_and_y(df_target, model_type, threshold)
    model.fit(X_train, y_train)

    if model_type == 'classifier':
        return y_test, df_target['prev_patch_pb%'].fillna(0), model.predict_proba(X_test)[:, 1]
    elif model_type == 'regressor':
        return y_test, df_target['prev_patch_pb%'].fillna(0), model.predict(X_test)
    else:
        print "Type must be regressor or classifier"
        return


def plot_scatter(y_true, y_pred, patch_num, rescale=False, log=False):
    if rescale:
        y_pred = y_pred * 2000 / np.sum(y_pred)  # use fact that sum of predictions should be 2000%
    plt.figure(figsize=(10, 8))
    if log:
        plt.xlim(-0.5, 5)
        plt.ylim(-0.5, 5)
        plt.xlabel('Actual pick+ban% (log scale)')
        plt.ylabel('Predicted pick+ban% (log scale)')
    else:
        plt.xlim(-5, 100)
        plt.ylim(-5, 100)
        plt.xlabel('Actual pick+ban%')
        plt.ylabel('Predicted pick+ban%')
    plt.title('Patch {0} Hero Drafting'.format(patch_num))
    plt.plot([-10, 100], [-10, 100], linestyle='--', color='dimgrey')
    if log:
        plt.scatter(np.log(y_true), np.log(y_pred), label='heroes', color='#0072B2')
    else:
        plt.scatter(y_true, y_pred, label='heroes', color='#0072B2')
    plt.legend(scatterpoints=1, loc='upper left')
    plt.show()
