import multiprocessing
import os

# Server socket
bind = '0.0.0.0:' + str(int(os.environ.get('PORT', 8000)))

# Worker processes
workers = 3
worker_class = 'sync'
worker_connections = 1000
max_requests = 5000
max_requests_jitter = 500

# Timeouts
timeout = 300  # 5 minutes
keepalive = 5  # 5 seconds

# Logging
accesslog = '-'  # Log to stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sms'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
