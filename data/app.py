from flask import Flask, request, Response
import time, json

app = Flask(__name__)

@app.post('/api')
def api():
    try:
        data = request.get_json()
        data['time'] = time.time()
        data['ip'] = request.remote_addr
        data['user_agent'] = request.user_agent.string
        with open(str(time.time()) + '.json', 'w') as f:
            json.dump(data, f)
        return Response(status=200)
    except Exception as e:
        return Response(status=500)