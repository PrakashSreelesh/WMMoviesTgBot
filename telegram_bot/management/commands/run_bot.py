from django.core.management.base import BaseCommand
from telegram_bot.telegram_handler import configure_bot  # Adjust path if necessary


class Command(BaseCommand):
    help = "Run the Telegram bot"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting Telegram bot...")
        application = configure_bot()  # Get the Application instance
        application.run_polling()  # Use run_polling to start the bot
