import docker
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.triggers.cron import CronTrigger
import logging

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.INFO)

def my_listener(event):
    if event.exception:
        print('The job crashed :(')
    else:
        print('The job worked :)')

client = docker.from_env()
scheduler = BackgroundScheduler({'apscheduler.timezone': 'America/Phoenix'})
scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
scheduler.start()

def exec(command, containerid):
    container = client.containers.get(containerid)
    container.exec_run(cmd=command)

while True:
    cur_jobs = []
    for container in client.containers.list():
        for key in container.labels:
            if key.startswith('job') and key.endswith('schedule'):
                scheduler.add_job(id = key.split('.')[1], name = key.split('.')[1], func=exec, trigger=CronTrigger.from_crontab(container.labels[key]), replace_existing=True, args=[container.labels['job.' + key.split('.')[1] + '.command'], container.id])
                cur_jobs.append(key.split('.')[1])
        
        for job in scheduler.get_jobs():
            if job.name not in cur_jobs:
                scheduler.remove_job(job.id)

    sleep(60)
