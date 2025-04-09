from pydantic import AwareDatetime, BaseModel, ConfigDict, HttpUrl, alias_generators


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
    date_time: AwareDatetime
    duration: str
    end_time: AwareDatetime
    event_url: HttpUrl
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
