import datetime
from functools import wraps
from pathlib import Path

from calmlib.autocast import autocast_args
from calmlib.read_write import load, dump
from calmlib import Timestamp, Timedelta, format_date
from simple_task_repeater.task_schedule import TaskSchedule


class TaskRepeater:
    def __init__(self, config_path: Path = None, db_path: Path = None, verbose=False):
        if config_path is None:
            config_path = Path('./task_repeater_config.pkl')
        self.config_path = config_path
        self._task_schedules = {}
        if config_path.exists():
            self.load_schedule()
        self.verbose = verbose

    @wraps(TaskSchedule.__init__)
    def add_task_schedule(self, **kwargs):
        task_schedule = TaskSchedule(**kwargs)
        self._task_schedules[task_schedule.key] = task_schedule
        self.dump_schedules()

    def load_schedule(self):
        self._task_schedules = {key: TaskSchedule(**val) for key, val in load(self.config_path).items()}

    def dump_schedules(self):
        dump({key: val.__dict__ for key, val in self.task_schedules.items()}, self.config_path)

    @property
    def task_schedules(self):
        return self._task_schedules

    def list_all_tasks(self):
        return {ts.key: ts.task for ts in self.task_schedules.values()}

    @autocast_args()
    def get_tasks(self, date: Timestamp = None):
        if date is None:
            # today
            date = Timestamp.now()
        self.verbose and print(f"Getting tasks for {format_date(date)}")
        tasks = []
        for key, task_schedule in self.task_schedules.items():
            if (date.date() - task_schedule.startdate.date()) % task_schedule.period == Timedelta(0):
                # todo: self.last_date[key]
                # todo: enddate
                tasks.append(task_schedule.task)
        return tasks

    @autocast_args()
    def register_task(self, key, date: Timestamp = None):
        # todo: actually log
        self._task_schedules[key].startdate = date
        self.dump_schedules()
