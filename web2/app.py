import time

import redis
from flask import Flask
from flask import Flask, json, render_template
import platform,socket,re,uuid,json,psutil,logging

companies = [{"id": 1, "name": "Arctiq"}, {"id": 2, "name": "Scalar"}]

app = Flask(__name__)
cache = redis.Redis(host='redis', port=6379)

def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr('hits')
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)

@app.route("/")
def subway():
    return render_template("index.html")

@app.route("/getinfo", methods=['GET'])
def getSystemInfo():
    count = get_hit_count()
    try:
        info={}
        info['hits']='{}'.format(count)
        info['platform']=platform.system()
        info['platform-release']=platform.release()
        info['platform-version']=platform.version()
        info['architecture']=platform.machine()
        info['hostname']=socket.gethostname()
        info['ip-address']=socket.gethostbyname(socket.gethostname())
        info['mac-address']=':'.join(re.findall('..', '%012x' % uuid.getnode()))
        info['processor']=platform.processor()
        info['ram']=str(round(psutil.virtual_memory().total / (1024.0 **3)))+" GB"
        return json.dumps(info)
    except Exception as e:
        logging.exception(e)

@app.route('/companies', methods=['GET'])
def get_companies():
  return json.dumps(companies)

@app.route('/hits')
def hello():
    count = get_hit_count()
    return 'web2:{} hits.\n'.format(count)

