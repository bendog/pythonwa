from pydantic import AwareDatetime, BaseModel, Field, RootModel, computed_field


class PythonWAVenue(BaseModel):
    name: str
    address_1: str = Field(alias="address", default="")
    city: str = Field(default="")


class PythonWAEvent(BaseModel):
    name: str
    date_time: AwareDatetime
    venue: PythonWAVenue
    attendance: int
    description: str
    link: str

    @computed_field
    @property
    def time(self) -> int:
        return int(self.date_time.timestamp() * 1000)


PythonWAEvents = RootModel[list[PythonWAEvent]]
