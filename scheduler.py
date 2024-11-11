from tinydb import Query, TinyDB
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from jobs import book_session_job, check_for_new_sessions_job
from variables import TINY_DB_PATH

class JobEnum(Enum):
    BookSession = 1
    CheckForNewSessions = 2

JobFuncLookup = {
    JobEnum.BookSession: book_session_job,
    JobEnum.CheckForNewSessions: check_for_new_sessions_job,
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

# Recurring jobs, in the format: JobEnum, (approx) seconds between execution
RECURRING_JOBS = [
    (JobEnum.CheckForNewSessions, 1800)
]

class Scheduler:
    def __init__(self, jobs_table, recurring_job_table):
        self.jobs_table = jobs_table
        self.recurring_job_table = recurring_job_table
    
    def schedule_job(self, job: Job):
        self.jobs_table.insert(job.to_dict())
    
    def run_jobs_due(self):
        self._run_oneshot_jobs_due()
        # self._run_recurring_jobs_due()
    
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
    
    # Currently unused
    def _run_recurring_jobs_due(self):
        for r_job in RECURRING_JOBS:
            RJob = Query()
            rjob_entry = self.recurring_job_table.get(RJob.job_enum)
            time_now = datetime.now()
            if (rjob_entry is None or 
                (time_now - datetime.fromtimestamp(rjob_entry['last_executed'])).total_seconds() > r_job[1]):
                func = JobFuncLookup[r_job[0]]
                try:
                    func()
                except:
                    pass
                if rjob_entry is not None:
                    self.recurring_job_table.update({'last_executed': time_now.timestamp()}, RJob.job_enum == r_job[0].value)
                else:
                    self.recurring_job_table.insert({'job_enum': r_job[0].value,'last_executed': time_now.timestamp()})

db = TinyDB(TINY_DB_PATH)
scheduler = Scheduler(jobs_table=db.table('jobs'), recurring_job_table=db.table('recurring_jobs'))
scheduler.run_jobs_due()