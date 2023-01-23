import socket
import time
from datetime import datetime

import api
from config import config
from workflow import Workflow
from celery_app import app as celery_app


def has_recent_activity(dir_path, recency_threshold=3600):
    # has anything been modified in the specified directory recently?
    last_update_time = max([p.stat().st_mtime for p in dir_path.iterdir()], default=time.time())
    return time.time() - last_update_time <= recency_threshold

def get_registered_batch_paths():
    batches = api.get_all_batches()
    return [b.origin_path for b in batches]

class Registration:
    def __init__(self):
        self.host = socket.getfqdn()
        self.source_dirs = set(Path(sd).resolve() for sd in config['registration']['source_dirs'] if Path(sd).exists())
        self.rejects = set(config['registration']['rejects'])
        self.completed = set(get_completed_batch_paths())  # HTTP GET
        self.candidates = set()
        self.steps = [
            {
                'name': 'inspect',
                'task': 'workers.inspect.inspect_batch'
            },
            {
                'name': 'archive',
                'task': 'workers.archive.archive_batch'
            },
            {
                'name': 'stage',
                'task': 'workers.stage.stage_batch'
            },
            {
                'name': 'validate',
                'task': 'workers.validate.validate_batch'
            }
        ]
        
    def register(self):
        while True:
            if self.candidates:
                for candidate in self.candidates:
                    if not has_recent_activity(candidate):
                        self.register_candidate(candidate)
                        self.completed.add(candidate)
                        self.candidates.remove(candidate)
            else:
                time.sleep(self.config['wait_between_scans'])
                self.scan()

    def scan(self):
        candidates = set()
        for source_dir in self.source_dirs:
            for p in sd.iterdir():
                if p.is_dir() and (str(p) not in self.completed):
                    candidates.add(p)
        return candidates

    def register_candidate(self, candidate):
        wf = Workflow(celery_app=celery_app, steps=self.steps)
        wf.start()
        batch = {
            'name': candidate.name,
            'origin_path': str(candidate.resolve()),
            'workflow_id': wf.workflow._id
        }
        # HTTP POST
        api.create_batch(batch)
        
