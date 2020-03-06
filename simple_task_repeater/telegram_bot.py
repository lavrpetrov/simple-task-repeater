import traceback
from functools import wraps

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from calmlib import get_personal_logger

logger = get_personal_logger(__name__)


def command_register(func):
    """

    :param func:
    :return:
    """
    func.command_register = None
    return func


def command_wrap(func):
    """
    Pass user and message to func instead of update and context
    :param func:
    :return:
    """
    func.command_wrap = None
    return func


def command(func):
    """
    Combines
    :param func:
    :return:
    """
    return command_register(command_wrap(func))


class TelegramBotMeta(type):
    def __new__(meta, name, bases, dct):
        def command(func):
            @wraps(func)
            def wrapper(self, update, context):
                user_name = update.effective_user.name
                message = update.effective_message.text
                logger.info(f"Received message, user: {user_name}, message: {message}")

                response = func(self, user_name, message=message)
                update.message.reply_text(response)
                logger.info(f"Sent response to user {user_name}, message: {response}")
                # todo: add switch - don't send debug messages to user?

            return wrapper

        commands = []
        for key, value in dct.items():
            if hasattr(value, 'command_wrap'):
                dct[key] = command(value)
            if hasattr(value, 'command_register'):
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

        dp.add_handler(MessageHandler(Filters.text, self.message_handler))

        # log all errors
        dp.add_error_handler(self.error_handler)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()

    @command_wrap
    def message_handler(self, user_name, message):
        """Echo the user message."""

        reply = ""
        reply += f"Hey {user_name}!\n"
        reply += f"{message} to you too!\n"
        reply += f"Use \\help commmand to get more info!\n"
        return reply

    def error_handler(self, update, context):
        """Log Errors caused by Updates."""
        logger.error('Update "%s" caused error "%s"', update, context.error)


def catch_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return f"Method {func.__name__} failed, exception: {traceback.format_exc()}"

    return wrapper
