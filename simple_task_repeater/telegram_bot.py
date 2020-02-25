import traceback
from functools import wraps

from telegram.ext import Updater, CommandHandler

from calmlib import get_personal_logger

logger = get_personal_logger(__name__)


def error_handler(update, context):
    """Log Errors caused by Updates."""
    logger.error('Update "%s" caused error "%s"', update, context.error)


def command(func):
    func.is_command = None
    return func


class TelegramBotMeta(type):
    def __new__(meta, name, bases, dct):
        def command(func):
            @wraps(func)
            def wrapper(self, update, context):
                user = update.effective_user.name
                message = update.effective_message.text
                logger.info(f"Received message, user: {user}, message: {message}")

                response = func(self, user=user, message=message)
                update.message.reply_text(response)
                logger.info(f"Sent response to user {user}, message: {response}")
                # todo: add switch - don't send debug messages to user?

            return wrapper

        commands = []
        for key, value in dct.items():
            if hasattr(value, 'is_command'):
                dct[key] = command(value)
                commands.append(value.__name__)
        dct['commands'] = commands
        return super(TelegramBotMeta, meta).__new__(meta, name, bases, dct)


class TelegramBot(metaclass=TelegramBotMeta):
    def __init__(self, token, proxy_url=None):
        request_kwargs = {}
        if proxy_url is not None:
            request_kwargs['proxy_url'] = proxy_url
        self.updater = Updater(token, request_kwargs=request_kwargs, use_context=True)
        dp = self.updater.dispatcher
        for command in self.commands:
            dp.add_handler(CommandHandler(command, getattr(self, command)))

        # log all errors
        dp.add_error_handler(error_handler)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()


def catch_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return f"Method {func.__name__} failed, exception: {traceback.format_exc()}"

    return wrapper
