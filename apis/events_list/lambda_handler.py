import json
import logging
import re

import markdown
import requests
from aws_lambda_typing import context as lambda_context
from aws_lambda_typing import events
from cache_util import ttl_cache
from meetup_models import GroupByQuery, GroupEventsEdgeNode

logger = logging.getLogger(__name__)


MEETUP_GROUP_NAME: str = "pythonwa"
MEETUP_URL: str = "https://api.meetup.com/gql-ext"

DEFAULT_HEADERS: dict[str, str] = {
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
    "Content-Type": "application/json",
}

P_PATTERN: re.Pattern = re.compile(r"<p>(.+?)</p>")
URL_PATTERN: re.Pattern = re.compile(
    r"(<a href=\""
    r"((http|https)://)?[a-zA-Z0-9./?:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9.&/?:@\-_=#])+"
    r"]\("
    r"((http|https)://)?[a-zA-Z0-9./?:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9.&/?:@\-_=#])+"
    r"\" class=\"linkified\">)"
)
END_URL_PATTERN: re.Pattern = re.compile(r"</a>\)")
BR_PATTERN: re.Pattern = re.compile(r"\n")


def convert_paragraph(text: str) -> str:
    """fix things which might exist inside a paragraph"""
    fixed_md = URL_PATTERN.sub("", text)
    fixed_md = END_URL_PATTERN.sub(")", fixed_md)
    fixed_md = BR_PATTERN.sub("<br/>", fixed_md)
    return markdown.markdown(fixed_md, extensions=["attr_list"]) + "\n"


def convert_markdown(md_text: str) -> str:
    """convert markdown to html"""
    p_groups = P_PATTERN.findall(md_text)
    html: str = ""
    if p_groups:
        for md_para in p_groups:
            html += convert_paragraph(md_para)
    else:
        html += convert_paragraph(md_text)
    return html


@ttl_cache(maxsize=128, ttl=15 * 60)
def talks_future() -> list[dict[str, str]]:
    """Get list of future talks"""
    events_list = []
    query: dict[str, str] = {
        "query": """query ($urlname: String!) {
          groupByUrlname(urlname: $urlname) {
            id
            events(first: 3, filter: { status: ACTIVE }) {
              totalCount
              edges {
                node {
                  id
                  status
                  title
                  dateTime
                  duration
                  endTime
                  eventUrl
                  venues {
                    name
                    address
                    city
                  }
                  rsvps {
                    yesCount
                    noCount
                  }
                  description
                }
              }
            }
          }
        }
        """,
        "variables": {
            "urlname": MEETUP_GROUP_NAME,
        },
    }
    payload = json.dumps(query)
    response = requests.post(MEETUP_URL, headers=DEFAULT_HEADERS, data=payload)
    logger.info(f"{response.status_code=} - {response.url=}")
    if response.status_code == 200:
        logger.debug(f"{type(response.json())=}")
        logger.debug(f"{response.json()=}")
        query_response: GroupByQuery = GroupByQuery.model_validate_json(response.text)
        logger.debug(query_response)
        logger.debug(query_response.model_dump_json(indent=2))
        node_list: list[GroupEventsEdgeNode] = [
            x.node for x in query_response.data.group_by_urlname.events.edges
        ]
        node_list.sort(key=lambda d: d.date_time)
        for event in node_list:
            venue_text: str = (
                f"{event.venues[0].name} ({event.venues[0].address} {event.venues[0].city})"
                if event.venues
                else "Venue TBC"
            )
            events_list.append(
                {
                    "name": event.title,
                    "time": event.date_time.isoformat(),
                    "venue": venue_text,
                    "attendance": event.rsvps.yes_count,
                    "description": convert_markdown(event.description),
                    "link": str(event.event_url),
                }
            )
    logger.info(f"{len(events_list)=}")
    return events_list


def handler(event: events.APIGatewayProxyEventV1, context: lambda_context):
    try:
        logger.info(event)
        # data: dict = json.loads(event["body"])

        response_body: list[dict] = talks_future()
        logger.info(response_body)
        return {
            "statusCode": 200,
            "headers": DEFAULT_HEADERS,
            "body": json.dumps(response_body),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": DEFAULT_HEADERS,
            "body": json.dumps({"error": e.__class__, "message": str(e)}),
        }


if __name__ == "__main__":
    resp = talks_future()
    for x in resp:
        print(json.dumps(x, indent=2))
