import logging
from data.credentials import telegram_token
import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from selenium_scripts import get_session_id_and_date, book_session
from tinydb import TinyDB
from scheduler import Scheduler
from telegram_funcs import book
from variables import TINY_DB_PATH

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    application = ApplicationBuilder().token(telegram_token).build()
    scheduler = Scheduler(
        jobs_table=TinyDB(TINY_DB_PATH).table('jobs'),
        job_queue=application.job_queue
    )
    application.scheduler = scheduler
    start_handler = CommandHandler('book', book)
    application.add_handler(start_handler)
    application.run_polling()
