import requests
from flask import Flask, request, Response

app = Flask(__name__)

TARGET_BASE_URL = "http://10.233.186.47:8080"

# Forward all methods and all paths to the target VM
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    target_url = f"{TARGET_BASE_URL}/{path}"

    if request.query_string:
        target_url += f"?{request.query_string.decode('utf-8')}"

    # Strip hop-by-hop headers that must not be forwarded
    excluded_headers = {
        'host', 'content-length', 'transfer-encoding',
        'connection', 'keep-alive', 'upgrade', 'te', 'trailers'
    }

    forward_headers = {
        k: v for k, v in request.headers
        if k.lower() not in excluded_headers
    }

    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=forward_headers,
            data=request.get_data(),
            allow_redirects=False,
            timeout=30,
        )
    except requests.exceptions.ConnectionError:
        return Response("Bad Gateway: cannot reach target VM", status=502)
    except requests.exceptions.Timeout:
        return Response("Gateway Timeout", status=504)

    # Strip hop-by-hop headers from the upstream response too
    response_headers = [
        (k, v) for k, v in resp.headers.items()
        if k.lower() not in excluded_headers
    ]

    return Response(
        resp.content,
        status=resp.status_code,
        headers=response_headers
    )
