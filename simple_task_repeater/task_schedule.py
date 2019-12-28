from calmlib.autocast import autocast_args
from calmlib import Timedelta, Timestamp, format_date


class TaskSchedule:
    @autocast_args()
    def __init__(self, key, task, period: Timedelta, startdate: Timestamp = None, enddate: Timestamp = None, ):
        self.key = key
        self.task = task
        self.period = period
        self.startdate = startdate
        self.enddate = enddate

    def __getstate__(self):
        state = self.__dict__
        state['startdate'] = format_date(state['startdate'])
        return state

    def __repr__(self):
        return 'Task(' + ','.join(f"{k}: {v}" for k, v in self.__dict__.items()) + ')'
