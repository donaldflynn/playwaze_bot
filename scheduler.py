from tinydb import Query, TinyDB
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from jobs import scheduled_booking_task
from variables import TINY_DB_PATH


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

    def to_dict(self):
        return {
            "job_enum": self.job_enum.value,
            "time": self.time.timestamp(),
            "data": self.data,
        }
    
    @staticmethod
    def from_dict(dict):
        return Job(
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
            db = TinyDB(TINY_DB_PATH)
            jobs_table = db.table('jobs')
            JobsData = Query()
            jobs_table.remove((JobsData.job_enum == job_enum.value) & (JobsData.time == context.job.next_t.run_time.timestamp()))
    
    def schedule_job(self, job: Job):
        if job.time < datetime.now():
            raise ValueError("Cannot schedule job in the past")
        self.jobs_table.insert(job.to_dict())
        self.job_queue.run_once(
            self.job_queue_executer,
            (job.time - datetime.now()).total_seconds(),
            data={**job.data, "job_enum": job.job_enum.value}
        )
    
    def load_jobs_from_database(self):
        jobs_list = self.jobs_table.all()
        for job_dict in jobs_list:
            current_job = Job.from_dict(job_dict)
            self.job_queue.run_once(
                self.job_queue_executer,
                (current_job.time - datetime.now()).total_seconds(),
                data={**current_job.data, "job_enum": current_job.job_enum.value}
            )