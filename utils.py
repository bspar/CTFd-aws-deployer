import boto3

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from CTFd.models import db, Challenges, Files, Solves, WrongKeys, Keys, Tags, Teams, Awards, Hints, Unlocks

def instance_status(name):
    return 'OK'

def create_instance(ami, teamid):
    return '10.12.11.13'
