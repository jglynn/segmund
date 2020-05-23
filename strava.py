"""
A crappy Strava helper module
"""
from typing import Dict
import requests
import stravalib

hop_club = 631182
hop_segment_id = 5471799
hop_segments = {
    "5807848":"Get IT",
	"23523730":"Valley View Dip up to Stop Light",
	"4542329":"Baker Bonebreaker - Valley View to 62",
	"14889054":"Bren Eastbound Climb",
	"23734538":"Park Climb after Malibu to top corner",
	"5995685":"Mirror Lake to Hankerson"
}

#
def get_auth_url(client_id, current_domain):
    scopes = ['read','profile:read_all','activity:read_all']
    client = stravalib.Client()
    return client.authorization_url(client_id=client_id, scope=scopes, redirect_uri="{}/exchange_token".format(current_domain))

# Register a client with Strava on behalf of user
def register_user(client_id, secret, auth_code):

    client = stravalib.Client()
    token_response = client.exchange_code_for_token(client_id=client_id, client_secret=secret, code=auth_code)

    client.access_token = token_response['access_token']
    client.refresh_token = token_response['refresh_token']
    client.token_expires_at = token_response['expires_at']

    athlete = client.get_athlete()

    user = {
        "_id": str(athlete.id),
        "type": "user",
        "name": athlete.username,
        "firstname": athlete.firstname,
        "lastname": athlete.lastname,
        "access_token": client.access_token,
        "expires_at": client.token_expires_at,
        "refresh_token": client.refresh_token
    }

    return user

# Generate a new access token from refresh token
def refresh_access_token(client_id, secret, refresh_token):

    client = stravalib.Client()
    refresh_response = client.refresh_access_token(client_id=client_id, client_secret=secret, refresh_token=refresh_token)

    #TODO: Persist token and access info back with the user
    access_token = refresh_response['access_token']
    refresh_token = refresh_response['refresh_token']
    expires_at = refresh_response['expires_at']

    return access_token

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
    return leader_result

# Gather hop segment leaders for a given date
def hop_segment_leaders(app_cfg, date):

    #TODO:
    # - Query DB for HOP Activity Segment Data by date
    # - FE registered user where we don't have Segment Data yet:
    #    - take user's token and fetch activities for the requested date
    #    - find their HOP activity (activity with HOP segment)
    #    - gather Activity segment data & persist
    # - Build leaderboard from Data

    #For now, just use my token and hit legacy leaderboard API
    token = refresh_access_token(app_cfg['STRAVA_CLIENT_ID'], app_cfg['STRAVA_SECRET'], app_cfg['STRAVA_REFRESH_TOKEN'])

    segment_leaders = {}
    for (segment_id,name) in hop_segments.items():
        segment_leaders[name] = segment_leaderboard(segment_id, token, hop_club, "this_month")
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
