from pathlib import Path

from calmlib import autocast_args, load_json, get_personal_logger
from calmlib.read_write import get_token
from simple_task_repeater.str_app import STRApp
from simple_task_repeater.str_database import STRDatabase

DEFAULT_DB_PATH = 'STRAppData'
DEFAULT_DROPBOX_TOKEN_PATH = "/Users/calmquant/repos/simple-task-repeater/config/dropbox.token"
DEFAULT_TELEGRAM_TOKEN_PATH = "/Users/calmquant/repos/simple-task-repeater/config/instacomplimentbot.token"
DEFAULT_NORDVPN_SECRET_PATH = "/Users/calmquant/repos/simple-task-repeater/config/nordvpn.secret"
DEFAULT_NORDVPN_SERVER = "fi96.nordvpn.com:80"

logger = get_personal_logger(__name__)


def create_app(db_path: Path = DEFAULT_DB_PATH, dropbox_token_path: Path = DEFAULT_DROPBOX_TOKEN_PATH,
               telegram_token_path: Path = DEFAULT_TELEGRAM_TOKEN_PATH,
               enable_proxy: bool = False,
               nordvpn_secret_path: Path = DEFAULT_NORDVPN_SECRET_PATH,
               nordvpn_server=DEFAULT_NORDVPN_SERVER, dropbox_subpath=None, offline_mode=False):
    dropbox_token = get_token(dropbox_token_path)
    telegram_token = get_token(telegram_token_path)

    if enable_proxy:
        proxy_credentials = load_json(nordvpn_secret_path)
        proxy_url = f'http://{proxy_credentials["user"]}:{proxy_credentials["password"]}@{nordvpn_server}/'
    else:
        proxy_url = None
    # dropbox_folder_name # default None

    logger.info("Creating STR database")
    logger.debug(f"{db_path.absolute()}")
    db = STRDatabase(path=db_path, dropbox_token=dropbox_token,
                     dropbox_subpath=dropbox_subpath, offline_mode=offline_mode)
    logger.info("Creating STR App")
    app = STRApp(db=db, token=telegram_token, proxy_url=proxy_url)
    return app


# todo: separate CLI for adding tasks - not from telegram.
@autocast_args
def main(db_path: Path = DEFAULT_DB_PATH, dropbox_token_path: Path = DEFAULT_DROPBOX_TOKEN_PATH,
         telegram_token_path: Path = DEFAULT_TELEGRAM_TOKEN_PATH,
         enable_proxy: bool = False,
         nordvpn_secret_path: Path = DEFAULT_NORDVPN_SECRET_PATH,
         nordvpn_server=DEFAULT_NORDVPN_SERVER, dropbox_subpath=None, offline_mode=False):
    logger.info("Launching simple task repeater")
    app = create_app(db_path, dropbox_token_path, telegram_token_path, enable_proxy, nordvpn_secret_path, nordvpn_server,
                     dropbox_subpath, offline_mode=offline_mode)

    logger.info("Launching the app")
    app.run()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--dropbox-token-path",
                        default=DEFAULT_DROPBOX_TOKEN_PATH)
    parser.add_argument("--dropbox-subpath", default="STRDatabase")
    parser.add_argument("--enable-proxy", action='store_true')
    parser.add_argument("--telegram-token-path",
                        default=DEFAULT_TELEGRAM_TOKEN_PATH)
    parser.add_argument("--nordvpn-secret-path",
                        default=DEFAULT_NORDVPN_SECRET_PATH)
    parser.add_argument("--nordvpn-server", default=DEFAULT_NORDVPN_SERVER)
    parser.add_argument("--offline-mode", action='store_true')

    args = parser.parse_args()
    main(**args.__dict__)
