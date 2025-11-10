from selenium_scripts import book_session
import logging
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

async def scheduled_booking_task(context):
    """This function is called by job_queue at the scheduled time."""
    job_data = context.job.data  # Retrieve data passed to the job
    chat_id = job_data["chat_id"]
    session_id = job_data["session_id"]
    booking_time = datetime.fromtimestamp(job_data["booking_timestamp"], tz=ZoneInfo("Europe/London"))

    logger.info(f"Running scheduled booking task for session {session_id} at {booking_time}")

    try:
        # Run the blocking book_session function in a thread to avoid blocking event loop
        result = await asyncio.to_thread(book_session, session_id, booking_time)
        await context.bot.send_message(chat_id=chat_id, text=f"Booking done for session {session_id} at {booking_time}")
    except Exception as e:
        logger.error(f"Error running scheduled booking: {e}")
        await context.bot.send_message(chat_id=chat_id, text=f"Error while booking session: {e}")
