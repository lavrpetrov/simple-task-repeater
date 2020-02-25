from pathlib import Path

from calmlib import autocast_args, load_json, get_personal_logger
from calmlib.read_write import get_token
from simple_task_repeater.str_app import STRApp
from simple_task_repeater.str_database import STRDatabase

logger = get_personal_logger(__name__)


# todo: separate CLI for adding tasks - not from telegram.
@autocast_args
def main(db_path: Path, dropbox_token_path: Path, telegram_token_path: Path, nordvpn_secret_path: Path,
         nordvpn_server="fi96.nordvpn.com:80", dropbox_subpath=None):
    logger.info("Launching simple task repeater")
    dropbox_token = get_token(dropbox_token_path)
    telegram_token = get_token(telegram_token_path)

    proxy_credentials = load_json(nordvpn_secret_path)
    proxy_url = f'http://{proxy_credentials["user"]}:{proxy_credentials["password"]}@{nordvpn_server}/'
    # dropbox_folder_name # default None

    logger.info("Creating STR database")
    logger.debug(f"{db_path.absolute()}")
    db = STRDatabase(path=db_path, dropbox_token=dropbox_token,
                     dropbox_subpath=dropbox_subpath)
    logger.info("Creating STR App")
    app = STRApp(db=db, token=telegram_token, proxy_url=proxy_url)

    logger.info("Launching the app")
    app.run()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default='STRAppData')
    parser.add_argument("--dropbox-token-path",
                        default="/Users/calmquant/repos/simple-task-repeater/config/dropbox.token")
    parser.add_argument("--dropbox-subpath", default=None)
    parser.add_argument("--telegram-token-path",
                        default="/Users/calmquant/repos/simple-task-repeater/config/instacomplimentbot.token")
    parser.add_argument("--nordvpn-secret-path",
                        default="/Users/calmquant/repos/simple-task-repeater/config/nordvpn.secret")
    parser.add_argument("--nordvpn-server", default="fi96.nordvpn.com:80")

    args = parser.parse_args()
    main(**args.__dict__)
