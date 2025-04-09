from datetime import datetime

from pydantic import BaseModel, ConfigDict, alias_generators
from pydantic_core import Url


class MeetupBaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=alias_generators.to_camel)


class Venue(MeetupBaseModel):
    name: str
    address: str
    city: str


class RSVPS(MeetupBaseModel):
    yes_count: int
    no_count: int


class GroupEventsEdgeNode(MeetupBaseModel):
    id: str
    status: str
    title: str
    description: str
    date_time: datetime
    duration: str
    end_time: datetime
    event_url: Url
    venues: list[Venue]
    rsvps: RSVPS


class GroupEventsEdge(MeetupBaseModel):
    node: GroupEventsEdgeNode


class GroupEvents(MeetupBaseModel):
    total_count: int
    edges: list[GroupEventsEdge]


class Group(MeetupBaseModel):
    id: str
    events: GroupEvents


class GroupByUrlnameResponse(MeetupBaseModel):
    group_by_urlname: Group


class GroupByQuery(MeetupBaseModel):
    data: GroupByUrlnameResponse
