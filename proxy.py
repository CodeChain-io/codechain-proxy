#!/usr/bin/env python3
import argparse
from flask import Flask
from flask import request
import requests

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
    parser.add_argument('--debug', action='store_true',
                        help='enable debug mode')

    args = parser.parse_args()

    app = Flask(__name__)
    with open(args.whitelist) as f:
        app.whitelist = set(line.rstrip() for line in f)
    app.forward = args.forward

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
            return invalid_request()

        content = request.get_json(silent=True)
        if content is None:
            return parse_error()

        if 'id' not in content:
            return ""

        if 'method' in content and content['method'] in app.whitelist:
            try:
                forward_addr = 'http://localhost:{}'.format(app.forward)
                r = requests.post(forward_addr, json=content)
                return r.text
            except Exception as e:
                return internal_error(content['id'])
        elif 'method' in content:
            return method_not_found(content['id'])

    app.run(host=args.bind, port=args.port, debug=args.debug)