@echo off
set FORKED_BY_MULTIPROCESSING=1
set CELERY_BROKER_URL=redis://localhost:6379/0
set CELERY_RESULT_BACKEND=redis://localhost:6379/0
celery -A job_processing_system worker --loglevel=info --pool=solo
