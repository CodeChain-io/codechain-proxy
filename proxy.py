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

    args = parser.parse_args()

    app = Flask(__name__)
    with open(args.whitelist) as f:
        app.whitelist = set(line.rstrip() for line in f)
    app.forward = args.forward

    @app.route('/', methods = ['POST'])
    def proxy():
        if not request.is_json:
            return '\"Invalid JSON Format\"'
        content = request.get_json()

        if 'method' in content and content['method'] in app.whitelist:
            try:
                forward_addr = 'http://localhost:{}'.format(app.forward)
                r = requests.post(forward_addr, json=content)
                return r.text
            except:
                return 'Failed to get value from the rpc server'
        else:
            return '\"Filtered\"'

    app.run(host=args.bind, port=args.port)