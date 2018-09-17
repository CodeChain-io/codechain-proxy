# codechain-proxy
An RPC proxy server for CodeChain

## How to use

### Arguments 

- `--bind`: A binding address of a proxy. The default value is `"0.0.0.0"`.
- `--port`: A binding port of a proxy.
- `--forward`: A port to forward. The default value is `8080`.
- `--whitelist`: A path to a whitelist file. The default value is `"whitelist.txt"`.

### Using gunicorn[eventlet]
```
gunicorn --bind="0.0.0.0:8080" --worker-class=eventlet \
    'proxy:create(whitelist="whitelist.txt", forward=8081, log="proxy.log")'
# or simply
gunicorn --worker-class=eventlet 'proxy:create()'
```

### Writing the whitelist

Each line of a whitelist file contains one method name which you want to accept.

For example, if you want to accept `version` and `ping`, put the method names in each line like:

```
version
ping
```