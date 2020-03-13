from pathlib import Path

from simple_task_repeater.__main__ import create_app


def try_launch():
    try:
        str_app = create_app(offline_mode=False, db_path=Path('STRTestData'), dropbox_subpath='STRTestData')
    except ConnectionError:
        print("Connection error, running in offline mode")
        str_app = create_app(offline_mode=True, db_path=Path('STRTestData'), dropbox_subpath='STRTestData')
    print("App successfully created")
    return str_app


if __name__ == '__main__':
    try_launch()
