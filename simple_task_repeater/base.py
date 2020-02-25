import datetime
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Task:
    shortcut: str  # mandatory, key for accessing the task
    text: str  # mandatory, task text
    period: int  # how often task should be repeated
    user: str  # mandatory
    date: datetime.datetime  # date the task is scheduled for.
    completions: list = field(default_factory=list)  # when task was completed
    reschedule: bool = False  # whether to reschedule a task for the next day if it wasn't completed
