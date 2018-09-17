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

    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s in %(module)s] %(message)s')
    handler = RotatingFileHandler(log, maxBytes=0x100000, backupCount=3)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    def log(address, message, level=logging.INFO):
        app.logger.log(level, '[{}] {}'.format(address, message))

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
        raddr = request.remote_addr
        if not request.is_json:
            log(raddr, 'Received request is not JSON')
            return invalid_request()

        content = request.get_json(silent=True)
        if content is None:
            log(raddr, 'Failed to parse JSON request: {}'.format(request.data))
            return parse_error()

        if 'id' not in content:
            return ""

        if 'method' in content and content['method'] in app.whitelist:
            try:
                forward_addr = 'http://localhost:{}'.format(app.forward)
                r = requests.post(forward_addr, json=content)
                log(raddr, 'Successfully forwarded {} / Response {}'.format(content, r.text.strip()))
                return r.text
            except Exception as e:
                log(raddr, 'Failed to receive the response from the server: {}'.format(e))
                return internal_error(content['id'])
        elif 'method' in content:
            log(raddr, 'Filtered {}: {}'.format(content['method'], content))
            return method_not_found(content['id'])

    return app

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