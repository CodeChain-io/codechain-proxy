#!/usr/bin/env python3
import argparse
from flask import Flask
from flask import request
import requests
import logging
from logging.handlers import RotatingFileHandler

def create(whitelist="whitelist.txt", forward=8080, log="proxy.log", **kwargs):
    app = Flask(__name__)
    with open(whitelist) as f:
        app.whitelist = set(line.rstrip() for line in f)
    app.forward = forward

    handler = RotatingFileHandler(log, maxBytes=0x100000, backupCount=3)
    handler.setLevel(logging.INFO)
    handler.setFormatter(RequestFormatter())
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    def error_msg(code, msg, id):
        id = "null" if id is None else id
        return '{{"jsonrpc":"2.0","error":{{"code":{},"message":"{}"}},"id":{}}}\n'.format(code, msg, id)

    def parse_error():
        return error_msg(-32700, "Parse error", None), 500

    def invalid_request():
        return error_msg(-32600, "Invalid request", None), 400

    def method_not_found(id):
        return error_msg(-32601, "Method not found", id), 404

    def internal_error(id):
        return error_msg(-32603, "Internal error", id), 500

    @app.route('/', methods = ['POST'])
    def proxy():
        if not request.is_json:
            app.logger.error('Received request is not JSON')
            return invalid_request()

        content = request.get_json(silent=True)
        if content is None:
            app.logger.error('Failed to parse JSON request: {}'.format(request.data))
            return parse_error()

        if 'id' not in content:
            return ""

        if 'method' in content and content['method'] in app.whitelist:
            try:
                forward_addr = 'http://localhost:{}'.format(app.forward)
                r = requests.post(forward_addr, json=content)
                app.logger.info('Successfully forwarded {} / Response {}'.format(content, r.text.strip()))
                return r.text
            except Exception as e:
                app.logger.error('Failed to receive the response from the server: {}'.format(e))
                return internal_error(content['id'])
        elif 'method' in content:
            app.logger.error('Filtered {}: {}'.format(content['method'], content))
            return method_not_found(content['id'])

    return app

class RequestFormatter(logging.Formatter):
    def __init__(self, fmt=None, **kwargs):
        default_fmt = '[%(asctime)s] [%(levelname)s in %(module)s] [%(remote_addr)s] %(message)s'
        if fmt is None:
            super().__init__(fmt=default_fmt, **kwargs)
        else:
            super().__init__(**kwargs)

    def format(self, record):
        record.remote_addr = request.remote_addr
        return super(RequestFormatter, self).format(record)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--whitelist', default='whitelist.txt',
                        help='whitelist file path (default: \"whiltelist.txt\")')
    parser.add_argument('--bind', default='0.0.0.0',
                        help='binding address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int,
                        help='binding port')
    parser.add_argument('--forward', type=int, default=8080,
                        help='port to forward (deafult: 8080)')
    parser.add_argument('--log', default='proxy.log',
                        help='log file path (default: \"proxy.log\")')
    parser.add_argument('--debug', action='store_true',
                        help='enable debug mode')

    args = parser.parse_args()
    app = create(**vars(args))
    app.run(host=args.bind, port=args.port, debug=args.debug)