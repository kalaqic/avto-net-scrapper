import uuid
from datetime import datetime
from typing import Dict, Optional
from src.api.models import ScrapeStatus
import pandas as pd
from src.shared.log import logger


class JobManager:
    """Manages scrape jobs and their results"""
    
    def __init__(self):
        self.jobs: Dict[str, dict] = {}
    
    def create_job(self, filters: dict) -> str:
        """Create a new scrape job and return job ID"""
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "job_id": job_id,
            "status": ScrapeStatus.PENDING,
            "filters": filters,
            "created_at": datetime.now(),
            "completed_at": None,
            "results": None,
            "error": None,
            "total_listings": 0
        }
        logger.info(f"Created new scrape job: {job_id}")
        return job_id
    
    def update_job_status(self, job_id: str, status: ScrapeStatus, error: Optional[str] = None):
        """Update job status"""
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            if error:
                self.jobs[job_id]["error"] = error
            if status == ScrapeStatus.COMPLETED or status == ScrapeStatus.FAILED:
                self.jobs[job_id]["completed_at"] = datetime.now()
            logger.info(f"Job {job_id} status updated to: {status}")
    
    def set_job_results(self, job_id: str, results: pd.DataFrame):
        """Store scrape results for a job"""
        if job_id in self.jobs:
            self.jobs[job_id]["results"] = results
            self.jobs[job_id]["total_listings"] = len(results) if results is not None else 0
            self.jobs[job_id]["status"] = ScrapeStatus.COMPLETED
            self.jobs[job_id]["completed_at"] = datetime.now()
            logger.info(f"Job {job_id} completed with {self.jobs[job_id]['total_listings']} listings")
    
    def get_job(self, job_id: str) -> Optional[dict]:
        """Get job information"""
        return self.jobs.get(job_id)
    
    def get_job_results(self, job_id: str) -> Optional[pd.DataFrame]:
        """Get job results as DataFrame"""
        job = self.jobs.get(job_id)
        if job and job.get("results") is not None:
            return job["results"]
        return None


# Global job manager instance
job_manager = JobManager()

