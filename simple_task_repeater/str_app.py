import datetime
from functools import wraps

from dateparser import parse as parse_date

from calmlib import get_current_date, get_current_datetime, to_date
from .base import Task
from .str_database import STRDatabase
from .telegram_bot import TelegramBot, command, catch_errors

DEFAULT_PERIOD = 4
TASK_PER_DAY_LIMIT = 3


class STRApp(TelegramBot):
    @wraps(TelegramBot.__init__)
    def __init__(self, db: STRDatabase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self._actualize_tasks()
        self._last_actualize_timestamp = get_current_datetime()

    @staticmethod
    def _tokenize_message(message):
        result = {}
        # cut off command code and get shortcut.
        _, result['shortcut'], message = message.split(maxsplit=2)
        parts = message.split(':')
        key = "text"
        for part in parts[:-1]:
            result[key], key = map(str.strip, part.rsplit(maxsplit=1))
        result[key] = parts[-1].strip()
        if not result['text']:
            del result['text']
        return result

    def _parse_task(self, user, task):
        """
        """
        if 'date' in task:
            try:
                task['date'] = parse_date(task['date'])
            except:
                raise ValueError(f"Failed to parse date {task['date']}")
        else:
            task['date'] = self._determine_suitable_date(user)
        if 'period' in task:
            task['period'] = int(task['period'])
        else:
            task['period'] = self._determine_suitable_period(user)
        return task

    def _determine_suitable_period(self, user):
        # todo: count current tasks and estimate period necessary to stay below task_per_day_limit
        #  discard large-period tasks.
        return DEFAULT_PERIOD

    def _determine_suitable_date(self, user):
        # todo: find the nearest date with < task_per_day_limit (3) tasks.
        return get_current_datetime()

    def parse_message(self, user, message):
        return self._parse_task(user, STRApp._tokenize_message(message))

    @command
    @catch_errors
    def add(self, user, message):
        """
        Add new task from message
        Message should have format
        {shortcut} {task text} period:1 {key}:{value}
        """
        result = ""
        task = {'user': user}
        task.update(self.parse_message(user, message))
        # todo: if date is not specified pick something suitable.
        # todo: if period is not specified - pick something suitable depending on current load
        task = Task(**task)
        self.db.add_task(task)
        result += f"Added task {task.shortcut}"
        return result

    @command
    @catch_errors
    def update(self, user, message):
        update = self.parse_message(user, message)
        task = self.db.get_task(user, update['shortcut'])

        task.__dict__.update(update)

        self.db.update_task(user, task)
        return f"Successfully updated task {task.shortcut}"

    @command
    @catch_errors
    def remove(self, user, message):
        """
        Remove task.
        """
        task = self.parse_message(user, message)
        self.db.remove_task(user, task['shortcut'])
        return f"Task {task['shortcut']} removed"

    @command
    @catch_errors
    def get(self, user, message):
        """
        Remove task.
        """
        task = self.parse_message(user, message)
        task = self.db.get_task(user, task['shortcut'])
        return repr(task)

    @command
    @catch_errors
    def start(self, user, message):
        try:
            self.db.add_user(user)
        except ValueError:
            return f"User {user} already active"
        return f"Added user {user} successfully"

    @command
    @catch_errors
    def stop(self, user, message):
        try:
            self.db.remove_user(user)
        except ValueError:
            return f"No user {user}"
        return f"Removed user {user} successfully"

    @command
    def list_all(self, user, message):
        """
        List shortcuts of users tasks
        """
        # todo: make a short task repr.
        return '\n'.join([task.shortcut for task in self.db.get_users_tasks(user)])

    @command
    def list(self, user, message):
        """
        Get tasks for particular date.

        """
        if message:
            date = parse_date(message)
        else:
            date = get_current_datetime()

        self.actualize_tasks()
        tasks = self.db.get_users_tasks(user)

        # need to cast into date because date is datetime with hours etc.
        tasks = [task for task in tasks if to_date(task.date) == to_date(date)]

        return "\n".join(map(repr, tasks))

    @command
    def complete(self, user, message):
        task = self.parse_message(user, message)
        if 'date' in task:
            date = parse_date(task['date'])
        else:
            date = get_current_datetime()
        task = self.db.get_task(user=user, shortcut=task['shortcut'])
        task.completions.append(date)
        task.date = date + datetime.timedelta(days=task.period)
        self.db.update_task(task)
        raise NotImplemented

    @command
    def help(self, user, message):
        """
        Return commands and shortened docstrings.
        """
        # todo: add docstrings - instead of help message for each command.
        # todo: how to make telegram list all possible commands?
        return '\n'.join([command.__name__ for command in self.commands])

    def run(self):
        with self.db:
            super().run()

    def actualize_tasks(self):
        if self._last_actualize_timestamp < get_current_date():
            self._actualize_tasks()
            self._last_actualize_timestamp = get_current_datetime()

    def _actualize_tasks(self):
        """
        Go over all tasks and update date/reschedule
        """
        for user_tasks in self.db.users_tasks.values():
            for task in user_tasks:
                today = get_current_datetime()
                if to_date(task.date) < to_date(today):
                    if task.reschedule:
                        # if task is past due and to be rescheduled - reschedule it on today
                        task.date = today
                    else:
                        task.date += datetime.timedelta(days=task.period)
