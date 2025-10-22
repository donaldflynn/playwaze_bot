import logging
from data.credentials import telegram_token
from telegram.ext import ApplicationBuilder, CommandHandler,  ContextTypes
from selenium_scripts import get_session_id_and_date, book_session
from telegram import Update
from tinydb import TinyDB
from scheduler import Scheduler, Job, JobEnum
from data.credentials import user_id
import asyncio
from datetime import datetime, timedelta

TINY_DB_PATH = "data/tinydb.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received command from user %s", update.message.from_user.id)
    if update.message.from_user.id == user_id:
        if context.args:  # Check if there's any argument
            book_string = " ".join(context.args)  # Combine arguments into one string
            # Call the function with the book_string
            response = await handle_book_string(update, context.application.bot_data['scheduler'], book_string)
            if response is not None:
                await update.message.reply_text(response)
        else:
            await update.message.reply_text("Please provide a string to book, e.g., '/book abc'.")

async def handle_book_string(update: Update, scheduler: Scheduler, book_string: str):
    # You can add whatever logic you want here based on the book_string
    logger.info(f"Handling the string: {book_string}")
    try:
        session_id, start_time = await asyncio.to_thread(get_session_id_and_date, book_string)
        await update.message.reply_text(f"Extracted session ID: {session_id} and start time: {start_time}")

        booking_time = (start_time - timedelta(days=3))
        job_time = booking_time - timedelta(seconds=40) 
        if (job_time - datetime.now()).total_seconds() <= 0:
            await update.message.reply_text("Booking time has already passed! Trying to book now...")
            await asyncio.to_thread(book_session, session_id, booking_time)
            await update.message.reply_text(f"Booking done for session {session_id} at {booking_time}")
            return
        
        booking_job = Job(
            job_id=None,
            job_enum=JobEnum.BookSession,
            time=job_time,
            data={"chat_id": update.effective_chat.id, "session_id": session_id, "booking_timestamp": booking_time.timestamp()}
        )
        scheduler.schedule_job(booking_job)
        await update.message.reply_text(f"Booking scheduled for {booking_time}")

    except Exception as e:
        logger.error(f"Error handling book string {book_string}: {e}")
        await update.message.reply_text(f"Error: {repr(e)}")

    return

if __name__ == "__main__":
    application = ApplicationBuilder().token(telegram_token).build()
    scheduler = Scheduler(
        jobs_table=TinyDB(TINY_DB_PATH).table('jobs'),
        job_queue=application.job_queue
    )
    application.bot_data["scheduler"] = scheduler 
    start_handler = CommandHandler('book', book)
    application.add_handler(start_handler)
    application.run_polling()
