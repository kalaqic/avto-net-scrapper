import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_ERROR, JobExecutionEvent
import pytz
import time
import random
from src.shared.config import scheduler_params
from src.internal.scraper import scrape
from src.shared.headers import get_random_schedule_interval, is_night_time
from src.shared.log import logger

async def run_scrape_job():
    start = time.time()
    logger.info("Scheduled scrape triggered.")
    await scrape(init=False)
    end = time.time()
    logger.info(f"Scrape completed in {end - start:.2f} seconds.")

def handle_job_error(event: JobExecutionEvent):
    logger.error(f"Scheduled job failed: {event.exception}", exc_info=True)

async def schedule_next_run(scheduler, time_zone):
    """
    Schedule the next run with dynamic intervals based on time of day.
    """
    # Remove existing jobs
    scheduler.remove_all_jobs()
    
    if is_night_time():
        # Night time (00:00-06:00): Every hour
        interval_minutes = 60
        logger.info(f"Night mode: scheduling next run in {interval_minutes} minutes")
    else:
        # Day time: Random interval between 2-5 minutes
        interval_minutes = get_random_schedule_interval()
        logger.info(f"Day mode: scheduling next run in {interval_minutes} minutes")
    
    # Add job for the next run
    from datetime import datetime, timedelta
    next_run_time = datetime.now(time_zone) + timedelta(minutes=interval_minutes)
    
    scheduler.add_job(
        run_scrape_job_and_reschedule,
        'date',
        run_date=next_run_time,
        timezone=time_zone,
        args=[scheduler, time_zone]
    )

async def run_scrape_job_and_reschedule(scheduler, time_zone):
    """
    Run the scrape job and then schedule the next one.
    """
    start = time.time()
    logger.info("Scheduled scrape triggered.")
    await scrape(init=False)
    end = time.time()
    logger.info(f"Scrape completed in {end - start:.2f} seconds.")
    
    # Schedule the next run
    await schedule_next_run(scheduler, time_zone)

async def start_scheduler() -> None:
    scheduler = AsyncIOScheduler()
    scheduler.add_listener(handle_job_error, EVENT_JOB_ERROR)

    time_zone = pytz.timezone(scheduler_params['timezone'])
    scheduler.start()

    # Schedule the first run
    await schedule_next_run(scheduler, time_zone)
    
    next_run = scheduler.get_jobs()[0].next_run_time
    logger.info(f"Dynamic scheduler started — next run at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shut down gracefully.")