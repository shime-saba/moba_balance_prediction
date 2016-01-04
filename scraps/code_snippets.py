'''
current patch pbr is the target, so the next patch pbr shouldn't be used
as a feature. might be useful for visualization, though.
'''
if patch_num < max(drafts_dict.keys()):
    next_df = drafts_dict[patch_num+1]
    next_pbs = dict(next_df[['hero', 'pb%']].values)
    new_pb_list = []
    for hero in df['hero']:
        if hero in next_pbs:
            new_pb_list.append(next_pbs[hero])
        else:
            new_pb_list.append(None)
    df['next_patch_pb%'] = new_pb_list
else:
    df['next_patch_pb%'] = [None]*len(df)
