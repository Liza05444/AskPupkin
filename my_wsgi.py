def application(environ, start_response):
    get_params = environ.get('QUERY_STRING', '').split('&')
    get_params = {k: v for k, v in [param.split('=') for param in get_params if '=' in param]}

    request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    request_body = environ['wsgi.input'].read(request_body_size).decode('utf-8')
    post_params = {k: v for k, v in [param.split('=') for param in request_body.split('&') if '=' in param]}
    
    status = '200 OK'
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    start_response(status, headers)
    
    response = [
        "GET:\n",
        "\n".join(f"{k}: {v}" for k, v in get_params.items()),
        "\n\nPOST:\n",
        "\n".join(f"{k}: {v}" for k, v in post_params.items()),
        "\n"
    ]
    
    return [line.encode('utf-8') for line in response]
