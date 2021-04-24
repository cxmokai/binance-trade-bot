import queue
import threading
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
from .config import Config

class NotificationDingDingHandler:
    def __init__(self, config: Config):
        self.config = config
        if eval(self.config.OPEN_DINGDING_NOTIFICATION):
            self.queue = queue.Queue()
            self.start_worker()
            self.enabled = True
        else:
            self.enabled = False
    
    def generate_url(self):
        timestamp = str(round(time.time() * 1000))
        secret = self.config.DINGDING_NOTIFICATION_SECRET
        secret_enc = secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return '{}&timestamp={}&sign={}'.format(self.config.DINGDING_NOTIFICATION_WEBHOOK, timestamp, sign)
    
    def start_worker(self):
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        while True:
            message = self.queue.get()            
            params = { 'msgtype': 'text', 'text': { 'content': message } }
            url = self.generate_url()
            requests.post(url, json=params)
            self.queue.task_done()

    def send_notification(self, message):
        if self.enabled:
            self.queue.put(message)
