import json
import dota2api
import time
import cPickle as pickle
import os

if __name__ == '__main__':
    d2a = dota2api.Initialise()

    '''
    # this section was used to generate a list of ids for all league games.
    # after building the list once, I pickle it to avoid repeating api calls.

    league_ids = [league['leagueid'] for league in d2a.get_league_listing()['leagues']]
    league_match_ids = []
    for league_id in league_ids:
        cur_match_ids = []
        match_dict = d2a.get_match_history(league_id=league_id)
        remaining = match_dict['results_remaining']
        cur_match_ids.extend([match['match_id'] for match in match_dict['matches']])
        while remaining > 0:
            match_dict = d2a.get_match_history(league_id=league_id, start_at_match_id=cur_match_ids[-1]-1)
            remaining = match_dict['results_remaining']
            cur_match_ids.extend([match['match_id'] for match in match_dict['matches']])
        league_match_ids.extend(cur_match_ids)
        time.sleep(1)

    with open('match_list.pkl', 'w') as fp:
        pickle.dump(league_match_ids, fp)
    '''
    with open('match_list.pkl') as f:
        league_match_ids = pickle.load(f)

    for match_id in league_match_ids:
        if os.path.isfile('/home/ubuntu/matches/{0}.json'.format(match_id)):
            continue
        try:
            match_dict = d2a.get_match_details(match_id=match_id)
            with open('/home/ubuntu/matches/{0}.json'.format(match_id), 'w') as fp:
                json.dump(match_dict, fp)
            time.sleep(1)
        except:
            print "hit cap at {0}".format(time.strftime('%H:%M:%s', time.localtime()))
            time.sleep(30)
