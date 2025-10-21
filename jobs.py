from selenium_scripts import book_session
from gmail import send_reply_to_thread, Thread
from variables import TINY_DB_PATH
from tinydb import TinyDB
import logging
import asyncio

logger = logging.getLogger(__name__)

# def book_session_job(
#     booking_time, session_id, **kwargs
# ):
#     thread = Thread.from_dict(kwargs)
#     try:
#         book_session(session_id, booking_time)
#         send_reply_to_thread("Success", thread)
#     except Exception as e:
#         send_reply_to_thread(f"Error: {repr(e)}", thread)

async def scheduled_booking_task(context):
    """This function is called by job_queue at the scheduled time."""
    job_data = context.job.data  # Retrieve data passed to the job
    chat_id = job_data["chat_id"]
    session_id = job_data["session_id"]
    booking_time = job_data["booking_time"]

    logger.info(f"Running scheduled booking task for session {session_id} at {booking_time}")

    try:
        # Run the blocking book_session function in a thread to avoid blocking event loop
        result = await asyncio.to_thread(book_session, session_id, booking_time, use_chrome=True)
        await context.bot.send_message(chat_id=chat_id, text=f"Booking done for session {session_id} at {booking_time}")
    except Exception as e:
        logger.error(f"Error running scheduled booking: {e}")
        await context.bot.send_message(chat_id=chat_id, text=f"Error while booking session: {e}")
