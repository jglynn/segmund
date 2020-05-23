"""
A crappy Strava helper module
"""
from typing import Dict
import requests

import stravalib


strava_token_url = "https://www.strava.com/oauth/token"
strava_leaderboard_url = "https://www.strava.com/api/v3/segments/{}/leaderboard?&club_id={}&date_range={}&per_page={}"
hop_club = 631182
hop_segments = {
    "5807848":"Get IT",
	"23523730":"Valley View Dip up to Stop Light",
	"4542329":"Baker Bonebreaker - Valley View to 62",
	"14889054":"Bren Eastbound Climb",
	"23734538":"Park Climb after Malibu to top corner",
	"5995685":"Mirror Lake to Hankerson"
}

# Register a client with Strava on behalf of user
def register_user(client_id, secret, auth_code):

    strava_token_params = {
        'client_id': client_id,
        'client_secret': secret,
        'code': auth_code,
        'grant_type': 'authorization_code'
    }

    reg_user_resp = requests.post(strava_token_url, params=strava_token_params, headers={'Content-Type':'application/json'})

    if(reg_user_resp.status_code > 201):
        print("Error registering with Strava: {}".format(reg_user_resp.json()))
        return None

    reg_user_json = reg_user_resp.json()

    user = {
        "_id": str(reg_user_json['athlete']['id']),
        "type": "user",
        "name": reg_user_json['athlete']['username'],
        "firstname": reg_user_json['athlete']['firstname'],
        "lastname": reg_user_json['athlete']['lastname'],
        "access_token": reg_user_json['access_token'],
        "expires_at": reg_user_json['expires_at'],
        "refresh_token": reg_user_json['refresh_token']
    }

    return user

# Generate a new access token from refresh token
def refresh_access_token(client_id, secret, refresh_token):
    params = {
        'client_id': client_id,
        'client_secret': secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
        }
    token_req = requests.post(strava_token_url, params=params, headers={'Content-Type':'application/json'})
    # todo check response
    return token_req.json()['access_token']

# /* Given a segment, return club leaders for a given date range
# *
# * date_range accepts: this_year, this_month, this_week, today
# *
# * docs: https://developers.strava.com/docs/reference/#api-Segments-getLeaderboardBySegmentId
def segment_leaderboard(segment_id, token, club_id, date_range):
    print("getting segment leaderboard")
    client = stravalib.Client(token)
    leaderboard = client.get_segment_leaderboard(
        segment_id, club_id=club_id, timeframe=date_range)
    leader_result = [get_leaderboard_entry_dict(entry)
                     for entry in leaderboard]
    print(leader_result)
    return leader_result

# Gather hop segment leaders for a given date range
def hop_segment_leaders(token, date_range):
    segment_leaders = {}
    for (segment_id,name) in hop_segments.items():
        segment_leaders[name] = segment_leaderboard(segment_id, token, hop_club, date_range)
    return segment_leaders


def get_leaderboard_entry_dict(
        entry: stravalib.model.SegmentLeaderboardEntry) -> Dict:
    """Extract leaderboard entries to dict for table rendering.

    Args:
        entry: segment leaderboard entry extract elements

    Returns
        Dict with the following keys: athlete_name, elapsed_time, moving_time,
        start_date, start_date_local, rank
    """
    return {
        "athlete_name": entry.athlete_name,
        "elapsed_time": entry.elapsed_time,
        "moving_time": entry.moving_time,
        "start_date": entry.start_date,
        "start_date_local": entry.start_date_local,
        "rank": entry.rank}
    