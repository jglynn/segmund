"""
    Super cruddy date helpers, dont laugh.
"""
import time
from datetime import datetime, timedelta, tzinfo, date

simple_format = "%Y-%m-%d"

def is_expired(epoch_time):
    """True if current time has passed the provided epoch_time"""
    return time.time() > epoch_time

def recent_thursday():
    """Returns most recent Thursday as datetime"""
    today = date.today()
    offset = (today.weekday() - 3) % 7
    return (today - timedelta(days=offset))

def thursdays(number_of_days):
    """Returns list of string formatted dates for last 'number_of_days' Thursdays"""
    thursdays = []
    start_date = recent_thursday()
    for i in range(number_of_days):
        thursdays.append((start_date - timedelta(days=(i*7))).strftime(simple_format))
    return thursdays

def parse_date(simple_date):
    """Returns simple date as datetime"""
    return datetime.strptime(simple_date, simple_format)

def next_day(simple_date):
    """Returns next date as a string formatted date"""
    return (parse_date(simple_date) + timedelta(days=1)).strftime(simple_format)
