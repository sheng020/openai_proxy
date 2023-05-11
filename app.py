from flask import Flask, request, Response, Request, abort
import requests
import openai
from gevent import pywsgi

app = Flask(__name__)
server_url = 'https://api.openai.com'


@app.route('/', methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def proxy(path=''):
    # 获取客户端请求的URL、方法和数据
    client_url = f'{server_url}/{path}'
    client_headers = request.headers
    headers = {}
    for key, value in client_headers.items():
        headers[key] = value
    del headers['Host']

    if not headers.__contains__('Authorization'):
        response = Response("Authorization not set", status=403)
        return response

    authStrs = headers['Authorization'].split(' ')

    if (len(authStrs) != 2):
        response = Response("Authorization format error", status=403)
        return response

    # 获得token
    token = authStrs[1]

    request.url = client_url

    # 特殊处理sse
    if path.startswith('v1/completions') or path.startswith('v1/chat/completions'):

        stream = False
        if request.is_json:
            json = request.json
            stream = json['stream']
            
            

        if stream:
            headers['Cache-Control'] = 'no-cache'
            headers['Connection'] = 'keep-alive'
            headers['Accept'] = 'text/event-stream'

        request.headers = headers

        try:
            response = requests.post(request.url, stream=True, headers=request.headers,
                                  params=request.args, data=request.data, json=request.json, timeout=60000)

            return Response(response=response.iter_content(chunk_size=1024), status=200, content_type=response.headers['Content-Type'], mimetype="text/event-stream")
        except requests.exceptions.RequestException as e:
            return Response(e.response, status=404)
    elif path.startswith('v1/images/variations'):
        
        image = request.files['image'].read()
        n = request.form['n']
        size = request.form['size']
        try:
            response = openai.Image.create_variation(api_key=token, image=image, n=n, size=size)
            return Response(response=str(response))
        except:
            return Response(status=500, response="Request openai error")
        
    elif path.startswith('v1/images/generations'):
        try:
            
            if (request.is_json):
                json = request.json
                prompt = json['prompt']
                n = json['n']
                size = json['size']
                response = openai.Image.create(api_key=token, prompt=prompt, n=n, size=size)
                return Response(response=str(response))
            else:
                return Response(status=401, response='Unsupport content type')
        except:
            return Response(status=403, response='Image generations error')

    else:
        return Response(status=403, response='Unsupport request right now')


if __name__ == '__main__':
    server = pywsgi.WSGIServer(('0.0.0.0', 9000), app)
    server.serve_forever()
    #app.run(port=9000)
