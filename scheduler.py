from tinydb import Query, TinyDB
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from jobs import scheduled_booking_task
from variables import TINY_DB_PATH
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class JobEnum(Enum):
    BookSession = 1

JobFuncLookup = {
    JobEnum.BookSession: scheduled_booking_task,
}

@dataclass
class Job:
    job_enum: JobEnum
    time: datetime
    data: dict[str, any]
    job_id: Optional[int] = None

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "job_enum": self.job_enum.value,
            "time": self.time.timestamp(),
            "data": self.data,
        }
    
    @staticmethod
    def from_dict(dict):
        return Job(
            job_id=dict.get('job_id'),
            job_enum=JobEnum(dict['job_enum']),
            time=datetime.fromtimestamp(dict['time']),
            data=dict['data']
        )

class Scheduler:
    def __init__(self, jobs_table, job_queue):
        self.jobs_table = jobs_table
        self.job_queue = job_queue
        self.load_jobs_from_database()

    @staticmethod
    async def job_queue_executer(context):
        """This function is called by job_queue at the scheduled time."""
        job_data = context.job.data  # Retrieve data passed to the job
        job_enum = JobEnum(job_data["job_enum"])
        func = JobFuncLookup[job_enum]
        try:
            await func(context)
        finally:
            # Remove job from database after execution
            jobs_table = context.application.bot_data['scheduler'].jobs_table
            jobs_table.remove(doc_ids=[context.job.data["job_id"]])
    
    def schedule_job(self, job: Job):
        if job.time < datetime.now():
            raise ValueError("Cannot schedule job in the past")
        
        logger.info(f"Scheduling job {job.job_enum} at {job.time}")
        job_id = self.jobs_table.insert(job.to_dict())
        self.job_queue.run_once(
            self.job_queue_executer,
            (job.time - datetime.now()).total_seconds(),
            data={**job.data, "job_enum": job.job_enum.value, "job_id": job_id}
        )
    
    def load_jobs_from_database(self):
        jobs_list = self.jobs_table.all()
        logger.info(f"Loading {len(jobs_list)} jobs from database")
        for job_dict in jobs_list:
            job_id = job_dict.doc_id
            current_job = Job.from_dict(job_dict)
            self.job_queue.run_once(
                self.job_queue_executer,
                (current_job.time - datetime.now()).total_seconds(),
                data={**current_job.data, "job_enum": current_job.job_enum.value, "job_id": job_id}
            )