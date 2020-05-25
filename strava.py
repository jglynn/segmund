"""
A crappy Strava helper module
"""
from typing import Dict
import requests
import stravalib
import date_utils

class Strava:

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

    def __init__(self, config):
        self.client_id = config['STRAVA_CLIENT_ID']
        self.secret = config['STRAVA_SECRET']

    def get_auth_url(self, current_domain):
        """Construct the Segmund authorization URL for Strava"""
        scopes = ['read','profile:read_all','activity:read_all']
        client = stravalib.Client()
        return client.authorization_url(client_id=self.client_id, scope=scopes, redirect_uri="{}/exchange_token".format(current_domain))

    def register_user(self, auth_code):
        """Register a client with Strava on behalf of user"""
        client = stravalib.Client()
        token_response = client.exchange_code_for_token(client_id=self.client_id, client_secret=self.secret, code=auth_code)

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

    # /* Given a segment, return club leaders for a given date range
    # *
    # * date_range accepts: this_year, this_month, this_week, today
    # *
    # * docs: https://developers.strava.com/docs/reference/#api-Segments-getLeaderboardBySegmentId
    def segment_leaderboard(self, segment_id, token, club_id, date_range):
        client = stravalib.Client(token)
        leaderboard = client.get_segment_leaderboard(
            segment_id, club_id=club_id, timeframe=date_range)
        leader_result = [self.get_leaderboard_entry_dict(entry)
                         for entry in leaderboard]
        return leader_result

    # Gather hop segment leaders for a given date
    def hop_alltime_leaders(self, db):

        #TODO: Move this kind of stuff into DB service
        john = db['326452']
        johns_token = self.get_user_access_token(john, db)

        segment_leaders = {}
        for (segment_id,name) in self.hop_segments.items():
            segment_leaders[name] = self.segment_leaderboard(segment_id, johns_token, self.hop_club, "this_month")
        return segment_leaders

    def get_leaderboard_entry_dict(self,
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

    def get_hop_activities(self, db, hop_date):
        """
            Compile activity segment results for HOP on a given date

            Currently just gathers all data live via Strava API.

            TODO: Ideas...
             - Query DB for HOP Activity Segment Data by given date
             - FE registered user where we don't have Segment Data for that date:
                - Using their token, fetch HOP activity(ies?) for the requested date
                - Persist Activity Segment Data to DB
             - Build leaderboard from DB data
        """
        selector = {'type': {'$eq': 'user'}}
        users = db.get_query_result(selector)

        segment_leaders = {segment: [] for segment in self.hop_segments.values()}
        start_date = hop_date
        end_date = date_utils.next_day(start_date)

        print("Searching for activities between start_date={} and end_date={}".format(start_date, end_date))
        for user in users:
            activities = self.get_public_hop_activities(user, db, start_date, end_date)
            for activity in activities:
                for effort in activity.segment_efforts:
                    if str(effort.segment.id) in self.hop_segments.keys():
                        segment_leaders.get(effort.name).append({
                            "segment_name":effort.name,
                            "rank": "N/A",
                            "athlete_id": str(activity.athlete.id),
                            "athlete_name": "{}, {}".format(user['lastname'], user['firstname']),
                            "activity": activity.name,
                            "start_date_local": str(activity.start_date_local),
                            "elapsed_time": str(effort.elapsed_time),
                            "average_heartrate": str(effort.average_heartrate),
                            "average_watts": str(effort.average_watts)
                            })
        return segment_leaders

    def get_public_activities(self, user, db, start_date, end_date):
        """Return detailed public activities for a given user beteen two dates"""
        token = self.get_user_access_token(user, db)
        client = stravalib.Client(token)
        activities = client.get_activities(after=start_date, before=end_date)
        return map(lambda activity : client.get_activity(activity.id, True),
                    filter(lambda activity: not activity.private, activities))

    def get_public_hop_activities(self, user, db, start_date, end_date):
        """Return any activities that contain the hop segment"""
        return filter(lambda activity: self.has_hop_segment(activity),
                self.get_public_activities(user, db, start_date, end_date))

    def has_hop_segment(self, activity):
        """True if an activity contains the HOP segment"""
        return any(effort.segment.id == self.hop_segment_id
                        for effort in activity.segment_efforts)

    def get_user_access_token(self, user, db):
        """Return user access token, if expired refresh it and persis to DB"""
        if date_utils.is_expired(user['expires_at']):
            print("token is expired for user={}".format(user))
            client = stravalib.Client()
            refresh_response = client.refresh_access_token(client_id=self.client_id,
                client_secret=self.secret, refresh_token=user['refresh_token'])
            # update the user with their new token and expiration
            user_document = db[user['_id']]
            user_document['access_token'] = refresh_response['access_token']
            user_document['refresh_token'] = refresh_response['refresh_token']
            user_document['expires_at'] = refresh_response['expires_at']
            user_document.save()
            return refresh_response['access_token']
        else:
            return user['access_token']
