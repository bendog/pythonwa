import datetime
import json
import logging

import requests
from aws_lambda_typing import context as lambda_context, events, responses
from dateutil.relativedelta import relativedelta, TH
from pydantic import BaseModel, PositiveInt, HttpUrl, RootModel

from cache_util import ttl_cache

DEFAULT_HEADERS = {
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}

TZ_AWST = datetime.timezone(offset=datetime.timedelta(hours=8), name="+08:00")
EVENT_START_HOUR = 17
EVENT_START_MINUTE = 30

logger = logging.getLogger(__name__)


class Venue(BaseModel):
    name: str
    address_1: str
    city: str


class Event(BaseModel):
    name: str
    time: datetime.datetime
    venue: Venue
    attendance: int
    description: str
    link: HttpUrl

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp(),
        }


class EventList(RootModel):
    root: list[Event]


def is_future_date(dt: datetime.datetime) -> bool:
    """checks if a date is in the future"""
    return dt.date() >= datetime.datetime.now(tz=TZ_AWST).date()


def get_first_thursday(year: int, month: int) -> datetime.datetime:
    start_of_month = datetime.datetime(year=year, month=month, day=1, tzinfo=TZ_AWST)
    return start_of_month + relativedelta(weekday=TH(0))


def get_future_event_dates(count: int) -> list[datetime.datetime]:
    """get the future first thursdays skipping january"""
    response: list[datetime.datetime] = []
    check_date: datetime.datetime = datetime.datetime.now(tz=TZ_AWST)
    while len(response) < count:
        first_thursday = get_first_thursday(check_date.year, check_date.month).replace(
            hour=EVENT_START_HOUR, minute=EVENT_START_MINUTE, second=0, microsecond=0
        )
        if is_future_date(first_thursday) and first_thursday.month > 1:
            response.append(first_thursday)
        check_date = check_date.replace(
            year=check_date.year if check_date.month < 12 else check_date.year + 1,
            month=check_date.month + 1 if check_date.month < 12 else 2,
        )
    return response


@ttl_cache(maxsize=128, ttl=15 * 60)
def talks_future() -> list[Event]:
    """Get list of future talks"""
    events_list = []
    response = requests.get("https://api.meetup.com/Perth-Django-Users-Group/events/")
    if response.status_code == 200:
        data = response.json()
        sorted_data = sorted(data, key=lambda d: d["time"])
        for event in sorted_data:
            events_list.append(
                Event(
                    name=event["name"],
                    time=event["time"],
                    venue=event.get("venue", ""),
                    attendance=event["yes_rsvp_count"],
                    description=event["description"],
                    link=event["link"],
                )
            )
    return events_list


def handler(
    event: events.APIGatewayProxyEventV1, context: lambda_context
) -> responses.APIGatewayProxyResponseV1:
    try:
        logger.info(event)
        # data: dict = json.loads(event["body"])

        response_body: EventList = EventList(root=talks_future())
        logger.info(response_body)
        return {
            "statusCode": 200,
            "headers": DEFAULT_HEADERS,
            "body": response_body.model_dump_json(),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": DEFAULT_HEADERS,
            "body": json.dumps({"error": e.__class__, "message": str(e)}),
        }
