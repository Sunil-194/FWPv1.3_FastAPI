from celery import Celery, signals
from dotenv import load_dotenv
from celery.result import AsyncResult
from time import sleep
import sys
import os
from .  import models
from . import routers
from . routers.fwp.fwp_genrate import api_call
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends
from datetime import datetime as dt
from dotenv import load_dotenv
import requests, json,os,traceback
load_dotenv()

celery = Celery(
    "fwp_job",
    broker= os.environ.get('CELERY_BROKER_URL'),
    backend=os.environ.get('CELERY_RESULT_BACKEND'),
    task_track_started = True
)

# celery.conf.accept_content = ['json']
# celery.conf.result_serializer = 'json'
# Configure connection pooling for Redis
# celery.conf.broker_pool_limit = 10  # Adjust the pool size as needed
# celery.conf.broker_pool_timeout = 30  # Adjust the timeout as needed

# Define the location of the task modules
# celery.conf.update(
#     task_routes={
#         "celery_worker": {"queue": "fwp_job"},  # Replace with your task module
#     },
#     task_serializer="json",
#     accept_content=["json"],
#     result_serializer="json",
# )


class SqlAlchemyTask(celery.Task):
    abstract = True

#//*---Sample FWP genrate job --------------------------------*//
@celery.task(name = 'create_task',base = SqlAlchemyTask)
def create_task(data):
    cwd = os.getcwd()
    save_path = os.path.join(cwd,'fwp_app','routers','fwp','Sample')
    api_call(data,save_path)
    print('done')


#//*---Function to update in db---*//
def update_record_in_db(task_id,state,status,traceback='None'):
    db = models.sessionlocal()
    
    try:
        record = db.query(models.task_log).filter_by(task_id=task_id).first()
        if record:
            ts = str(dt.now())
            record.status = status
            record.state = state
            record.updated_time = ts
            record.traceback = traceback
            db.commit()
            db.refresh(record)
               
    except Exception as e:        
        raise e
    finally:
        db.close()
        
        
#//*----Web hook notification---*//
def webhook_update(task_id,status,traceback='None'):
    webhook_url = os.environ.get('WEBHOOK_URL')
    req = {
        "task_id":task_id,
        "task_status":status,
        "task_traceback":traceback
    }
    # r = requests.post(webhook_url,data=json.dumps(req),headers={"Content-Type": "application/json"})
    r = requests.post(webhook_url,json=req,headers={"Content-Type": "application/json"})
    try:
        db = models.sessionlocal()
        record = db.query(models.task_log).filter_by(task_id=task_id).first()
        if record:
            record.webhook_status = 'done'
            db.commit()
                           
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.refresh(record)
        db.close()

    

#//*---Automatically called Task Sucess function---*// 
@signals.task_success.connect
def task_success_handler(sender=None, result=None,**kwargs):
    # Extract information from the result, such as task ID or any relevant data
    task_id = sender.request.id
    result = AsyncResult(task_id, app=celery)
    state = result.state
    status = result.status
 
    update_record_in_db(sender.request.id,result.state,result.status)
    ts = str(dt.now())
    webhook_update(task_id,status)


    
#//*---Automatically called Task Failure function---*// 
@signals.task_failure.connect
def task_failure_handler(sender=None, result=None,**kwargs):
    # Extract information from the result, such as task ID or any relevant data
    task_id = sender.request.id
    result = AsyncResult(task_id, app=celery)
    state = result.state
    status = result.status
    
    update_record_in_db(sender.request.id,result.state,result.status,result.traceback)
    ts = str(dt.now())
    webhook_update(task_id,status,traceback)