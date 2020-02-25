from functools import wraps

from .base import Task
from .database import Database, synced


class STRDatabase(Database):
    @wraps(Database.__init__)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not 'users_tasks' in self.data:
            self.data['users_tasks'] = {}  # users_tasks[user][task_key]
        if not 'removed_users' in self.data:
            self.data['removed_users'] = {}  # users_tasks[user][task_key]

    def get_users_tasks(self, user):
        if not self.has_user(user):
            raise ValueError(f"No user {user}")
        return list(self.users_tasks[user].values())

    def has_user(self, user):
        return user in self.users_tasks

    @synced
    def add_user(self, user):
        if self.has_user(user):
            raise ValueError(f"Already have user {user}")
        if user in self.removed_users:
            self.users_tasks[user] = self.removed_users[user]
            del self.removed_users[user]
        else:
            self.users_tasks[user] = {}

    @synced
    def remove_user(self, user):
        if not self.has_user(user):
            raise ValueError(f"No user {user}")
        self.removed_users[user] = self.users_tasks[user]
        del self.users_tasks[user]

    @property
    def users_tasks(self):
        return self.data['users_tasks']

    @property
    def removed_users(self):
        return self.data['removed_users']

    def has_task(self, user, shortcut):
        return self.has_user(user) and shortcut in self.get_users_tasks(user)

    @synced
    def add_task(self, task: Task):
        if not self.has_user(task.user):
            self.add_user(task.user)
        if self.has_task(task.user, task.shortcut):
            raise ValueError(f"Already have task {task.shortcut} for user {task.user}")
        self.users_tasks[task.user][task.shortcut] = task.to_json()

    def get_task(self, user, shortcut):
        if not self.has_task(user, shortcut):
            raise ValueError(f"No task {shortcut} for user {user}")
        return Task.from_json(self.users_tasks[user][shortcut])

    @synced
    def update_task(self, task: Task):
        if not self.has_task(task.user, task.shortcut):
            raise ValueError(f"No task {task.shortcut} for user {task.user}")
        self.users_tasks[task.user][task.shortcut] = task.to_json()

    @synced
    def remove_task(self, user, shortcut):
        if not self.has_task(user, shortcut):
            raise ValueError(f"No task {shortcut} for user {user}")
        del self.users_tasks[user][shortcut]
