from fastapi import FastAPI, Depends, status,Response,HTTPException, APIRouter,UploadFile,File,responses, BackgroundTasks
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

from celery.result import AsyncResult
from fastapi.encoders import jsonable_encoder

router = APIRouter(
    tags=['USER'],
    prefix='/fwp'
    
)
session_global_db = models.sessionlocal()


@router.post('/createfwp',status_code=status.HTTP_201_CREATED)
async def Create_FWP(json_file:UploadFile = File(...),db:Session=Depends(models.get_db)):
# async def Create_FWP(save_path:str,background_task:BackgroundTasks,json_file:UploadFile = File(...),db:Session=Depends(get_db)):

    try:
        print(json_file.content_type)
        if json_file.content_type == 'application/json':
            js_file = await json_file.read()
            # with open(json_file, encoding='utf-8') as fh:
            #     json_data = json.load(fh)
            json_data = json.loads(js_file)
        else:
            print('Wrong File2')
            responses.status_code = status.HTTP_406_NOT_ACCEPTABLE
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail="Please Insert a Json File")
        print(len(json_data['document']))
        task_response = []
        for i in range(len(json_data['document'])):
            print('\n\n ',i)
            data=json_data['document'][i]
            user_uuid = data['meta']['user_uuid']
            user_name = data['meta']['name']
            print(user_name)
        
            # task = celery_worker.celery.send_task('create_task',args=[data])
            task = celery_worker.create_task.apply_async(args=[data],countdown=5)
            print('\n\n\n Taks ID is : ',task.task_id)
            result = AsyncResult(task.task_id, app=celery_worker.celery)
            task_log(db, task.task_id,user_uuid,user_name,result.state,result.status)
            task_response.append({'task_id':task.task_id,"user_uuid":user_uuid,"user_name":user_name})
            
        webhook_url = os.environ.get('WEBHOOK_URL')
        req = {
            "response":task_response,
        }
        r = requests.post(webhook_url,data=json.dumps(req),headers={"Content-Type": "application/json"})
        return req

            
    except Exception as e:        
        error_log = {
            "Full Error":traceback.format_exc()
        }
        print(error_log)
        responses.status_code = status.HTTP_406_NOT_ACCEPTABLE
        raise HTTPException(status_code=responses.status_code,detail={"Status":"PDF Not Created Please Check Json Data","Error Log":error_log})
    
    finally:
        ts = str(dt.now())
        print('function processed')
        
        

def task_log(db, taskid,user_uuid,user_name,state,status):
    ts = str(dt.now())
    print(ts)
    task_log = models.task_log(uuid=user_uuid,name=user_name,task_id = taskid,created_time=ts,updated_time=ts,state = state,status=status)
    db.add(task_log)
    db.commit()
    db.refresh(task_log)
    db.close()
    print('Task log added')


# @router.post('/webhook_check',status_code=status.HTTP_201_CREATED)
# def check_webhook(request:schema.webhook_check):
#     webhook_url = os.environ.get('WEBHOOK_URL')
#     req = {
#         "name":request.name,
#         "number":request.number
#     }
#     r = requests.post(webhook_url,data=json.dumps(req),headers={"Content-Type": "application/json"})
#     return {'Name':r} 
    
        
