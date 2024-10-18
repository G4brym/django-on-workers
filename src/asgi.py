import os


def request_to_scope(req, env):
    from js import URL
    headers = []
    for header in req.headers:
        headers.append(tuple([header[0].encode('latin1'), header[1].encode('latin1')]))

    url = URL.new(req.url)
    scheme = url.protocol[:-1]
    path = url.pathname
    query_string = url.search[1:].encode()

    return {
        "asgi": {"spec_version": "2.0", "version": "3.0"},
        "type": "http",
        "http_version": "1.1",
        "method": req.method,
        "scheme": scheme,
        "path": path,
        "query_string": query_string,
        "headers": headers,
        # You might want to pass `env` if it's relevant for your Django app's context
        "env": env,
    }


async def process_request(app, req, env):
    from js import Object, Response

    from pyodide.ffi import create_proxy

    status = None
    headers = None
    result = None

    body = await req.arrayBuffer()
    body_stream = [
        {"body": body.to_bytes(), "more_body": True, "type": "http.request"},
        {"body": b"", "more_body": False, "type": "http.request"}
    ]

    async def receive():
        return body_stream.pop(0)
    #
    # async def response_gen():
    #     if req.body:
    #         async for data in req.body:
    #             yield {"body": data.to_bytes(), "more_body": True, "type": "http.request"}
    #     yield {"body": b"", "type": "http.request"}
    #
    # responses = response_gen()
    #
    # async def receive():
    #     return await anext(responses)

    async def send(got):
        nonlocal status
        nonlocal headers
        nonlocal result
        if got["type"] == "http.response.start":
            status = got["status"]
            headers = got["headers"]
        if got["type"] == "http.response.body":
            px = create_proxy(got["body"])
            buf = px.getBuffer()
            px.destroy()

            new_headers = []
            for header in headers:
                new_headers.append(tuple([
                    header[0].decode("latin1"),
                    header[1].decode("latin1"),
                ]))

            result = Response.new(
                buf.data, headers=Object.fromEntries(new_headers), status=status
            )

    await app(request_to_scope(req, env), receive, send)

    return result


async def on_fetch(req, env):
    from app.asgi import application
    os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", 'true')
    result = await process_request(application, req, env)

    return result
