from tinydb import Query, TinyDB
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from jobs import book_session_job
from variables import TINY_DB_PATH

class JobEnum(Enum):
    BookSession = 1

JobFuncLookup = {
    JobEnum.BookSession: book_session_job,
}

@dataclass
class Job:
    job_enum: JobEnum
    time: datetime
    kwargs: dict

    def to_dict(self):
        return {
            "job_enum": self.job_enum.value,
            "time": self.time.timestamp(),
            "kwargs": self.kwargs,
        }
    
    @staticmethod
    def from_dict(dict):
        return Job(
            job_enum=JobEnum(dict['job_enum']),
            time=datetime.fromtimestamp(dict['time']),
            kwargs=dict['kwargs']
        )

    def execute(self):
        func = JobFuncLookup[self.job_enum]
        func(self.kwargs)

class Scheduler:
    def __init__(self, jobs_table):
        self.jobs_table = jobs_table
    
    def schedule_job(self, job: Job):
        self.jobs_table.insert(job.to_dict())
    
    def run_jobs_due(self):
        self._run_oneshot_jobs_due()
    
    def _run_oneshot_jobs_due(self):
        time_now = datetime.now()
        JobsData = Query()
        jobs_list = self.jobs_table.search(JobsData.time < time_now.timestamp())
        # Error handling should be done inside the job. 
        # Pass out of any errors to delete the jobs and avoid getting stuck in a loop
        try:
            if len(jobs_list) != 0:
                for job_dict in jobs_list:
                    current_job = Job.from_dict(job_dict)
                    current_job.execute()
        except:
            pass
        self.jobs_table.remove(JobsData.time < time_now.timestamp())