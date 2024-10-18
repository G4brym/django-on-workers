import os
from io import BytesIO, StringIO


class PyodideWSGIAdapter:
    def __init__(self, app):
        self.app = app

    def handle_request(self, environ):
        from js import Object, Response

        # Response placeholder
        response_body = []
        # status = ''
        # headers = []

        def start_response(status_str, response_headers):
            nonlocal status, headers
            status = status_str
            headers = response_headers

        resp = self.app(environ, start_response)
        status = resp.status_code
        headers = resp.headers
        # print(dir(resp.content))
        # print(resp.headers)
        # print(resp.body)
        # return resp
        # Call the WSGI application
        # loop = asyncio.get_running_loop()
        # tsk = loop.create_task(self.app(environ, start_response))
        # tsk.add_done_callback(
            # lambda t: print(f'Task done with result={t.result()}  << return val of main()'))
        # app_iter = asyncio.run()
        # try:
        #     for item in app_iter:
        #         response_body.append(item)
        # finally:
        #     if hasattr(app_iter, 'close'):
        #         app_iter.close()

        # status = status.split(' ')[0]

        return Response.new(
            resp.content.decode('utf-8'), headers=Object.fromEntries(headers.items()), status=status
        )


async def on_fetch(request, env):
    os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')
    from js import URL, console
    headers = []
    for header in request.headers:
        headers.append(tuple([header[0], header[1]]))

    # print(headers)

    url = URL.new(request.url)
    assert url.protocol[-1] == ":"
    scheme = url.protocol[:-1]
    path = url.pathname
    assert "?".startswith(url.search[0:1])
    query_string = url.search[1:]
    method = str(request.method).upper()

    host = url.host.split(':')[0]

    from app.wsgi import application
    adapter = PyodideWSGIAdapter(application)

    wsgi_request = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'SERVER_NAME': host,
        'SERVER_PORT': url.port,
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.input': BytesIO(b''),
        'wsgi.errors': console.error,
        'wsgi.version': (1, 0),
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': True,
        'wsgi.url_scheme': scheme,
    }

    if request.headers.get('content-type'):
        wsgi_request['CONTENT_TYPE'] = request.headers.get('content-type')

    if request.headers.get('content-type'):
        wsgi_request['CONTENT_LENGTH'] = request.headers.get('content-length')

    for header in request.headers:
        wsgi_request[f'HTTP_{header[0].upper()}'] = header[1]

    if method in ['POST', 'PUT', 'PATCH']:
        # body = await request.text()
        body = (await request.arrayBuffer()).to_bytes()
        print(body)
        wsgi_request['wsgi.input'] = BytesIO(body)
        # wsgi_request['wsgi.input'] = StringIO(body)
        # wsgi_request['wsgi.input'] = BytesIO(body.to_bytes())

    return adapter.handle_request(wsgi_request)
