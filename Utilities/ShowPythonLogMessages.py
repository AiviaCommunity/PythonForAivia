import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

"""
Prints any new Python-related messages printed to the Aivia log to the Python console.

The log_dir variable points to the default Aivia log path for the latest stable
release by default. If it does not work for you, you need to set the log_dir variable
to the path shown in File > Options... > Logging > Folder.

Run this file either in Idle or in a CMD window using:
> python ShowPythonLogMessages.py

Stop logging by pressing CTRL+C in the console.

Note that this only updates the console as often as Aivia is set to flush to the log.
This can be changed in File > Options... > Logging.

Requirements
------------
watchdog
"""

log_dir = os.path.join(os.getenv('LOCALAPPDATA'),'DRVision Technologies LLC/Aivia 9.0.0.34168/')


class HandleLogUpdates(FileSystemEventHandler):
    """
    Prints lines relevant to Python usage from the Aivia log as they are added
    in near-real time.

    Modify self.messages in __init__ with more/less message codes and they will automatically
    be picked up by the watchdog.
    """

    def __init__(self):
        self.f = None
        self.messages = ['I Python', 'E Python', 'D PythonRecipe', 'E Measurement']
    
    def on_modified(self, event):
        """
        When the Aivia log is modified this is triggered. Lines from the log will
        only be printed if they are new and start with 'I Python'.
        """
        if event.src_path.endswith('.log'):
            if self.f is None:
                self.f = open(event.src_path, mode='r')
            for line in self.f.readlines():
                if any([line.startswith(m) for m in self.messages]):
                    print(line)

    def __del__(self):
        if self.f is not None:
            self.f.close()


update_handler = HandleLogUpdates()
observer = Observer()
observer.schedule(update_handler, log_dir, recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    del update_handler
