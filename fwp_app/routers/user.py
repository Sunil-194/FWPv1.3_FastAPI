from fastapi import FastAPI, Depends, Request, status,Response,HTTPException, APIRouter,UploadFile,File,responses, BackgroundTasks
from .. import models,schema
from sqlalchemy import MetaData
from sqlalchemy.orm import Session
from typing import List
import json,os,sys,traceback
from datetime import datetime as dt
import time
from celery.result import AsyncResult
import subprocess
import requests
from .. import celery_worker
from celery.contrib.abortable import AbortableTask
from celery.result import AsyncResult
from fastapi.encoders import jsonable_encoder
from .. schema import user_api


router = APIRouter(
    tags=['USER'],
    prefix='/fwp'
    
)
session_global_db = models.sessionlocal()


@router.post('/createfwp',status_code=status.HTTP_201_CREATED)
async def Create_FWP(api_fc_uuid:str,json_file:UploadFile = File(...),db:Session=Depends(models.get_db)):
# async def Create_FWP(save_path:str,background_task:BackgroundTasks,json_file:UploadFile = File(...),db:Session=Depends(get_db)):

    print(api_fc_uuid)
    try:
        print(json_file.content_type)
        if json_file.content_type == 'application/json':
            js_file = await json_file.read()
            json_data = json.loads(js_file)
            
        else:
            responses.status_code = status.HTTP_406_NOT_ACCEPTABLE
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail="Please Insert valid a Json File")
        
        task_response = []
        # for i in range(len(json_data['document'])):
        #     data=json_data['document'][i]
        #     user_uuid = data['meta']['user_uuid']
        #     user_name = data['meta']['name']

        for i,data in enumerate(json_data['document']):
            user_uuid_client = data['meta']['user_uuid']
            user_name = data['meta']['name']

            task = celery_worker.create_task.apply_async(args=[data],countdown=5)
            result = AsyncResult(task.task_id, app=celery_worker.celery)
            task_log(db, task.task_id,api_fc_uuid,user_uuid_client,user_name,result.state,result.status)
            task_response.append({'task_id':task.task_id,"user_uuid":user_uuid_client,"user_name":user_name})
        
        #//*----A webhook post request to show all the pdf creation passed by user having client FWP data in JSON with their uuid.     
        webhook_url = os.environ.get('WEBHOOK_URL')
        req = {
            "response":task_response,
        }
        r = requests.post(webhook_url,data=json.dumps(req),headers={"Content-Type": "application/json"})
        
        api_traceback = 'None'
        responses.status_code = status.HTTP_201_CREATED
        # status_code = responses.status_code  
        return req
            
    except Exception as e:        
        api_traceback = traceback.format_exc()
        error_log = {
            "Full Error":api_traceback
        }
        responses.status_code = status.HTTP_406_NOT_ACCEPTABLE
        status_code = responses.status_code
        raise HTTPException(status_code=responses.status_code,detail={"Status":"PDF Not Created Please Check Json Data","Error Log":error_log})
    finally:
        status_code = responses.status_code
        api_db_logs(db,api_fc_uuid,status_code,api_traceback)
    
        
        

def task_log(db, taskid,api_fc_uuid,user_uuid_client,user_name,state,status):
    ts = str(dt.now())
    task_log = models.task_log(fc_uuid=api_fc_uuid,user_uuid=user_uuid_client,name=user_name,task_id = taskid,created_time=ts,updated_time=ts,state = state,status=status)
    db.add(task_log)
    db.commit()
    db.refresh(task_log)
    db.close()

def api_db_logs(db,api_fc_uuid,status_code,api_traceback='None'):
    ts = str(dt.now())
    task_log = models.create_fwp_log(fc_uuid=api_fc_uuid,status=status_code,created_time=ts,updated_time=ts,traceback=api_traceback)
    db.add(task_log)
    db.commit()
    db.refresh(task_log)
    db.close()
    
    
# @router.post('/abort_tasks',status_code=status.HTTP_201_CREATED)
# def abort_running_task(**task_data):
#     # data = json.loads(task_data)
#     data = json.loads(task_data['task_data'])
#     for key in data['response']:
#         task_id = key['task_id']
        
        
#         task = AsyncResult(task_id, app=celery_worker.celery).revoke()
#         return 'canceled'
    


# @router.post('/webhook_check',status_code=status.HTTP_201_CREATED)
# def check_webhook(request:schema.webhook_check):
#     webhook_url = os.environ.get('WEBHOOK_URL')
#     req = {
#         "name":request.name,
#         "number":request.number
#     }
#     r = requests.post(webhook_url,data=json.dumps(req),headers={"Content-Type": "application/json"})
#     return {'Name':r} 
    
        
