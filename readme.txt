

#//*-----To Install Dependencies--------***//

-> pip install -r requirements.txt



//*---To run servers---*//
1. To run Ubuntu server 
    -> ubuntu
    -> redis-cli

2. To run Uvicorn server
    -> uvicorn fwp_app.main:app --reload

1. To run celery server
    -> celery -A fwp_app.celery_worker.celery worker -l info -P gevent


