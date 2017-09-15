import time

from rpc.rpc import RPC
from rpc.constants import LOCAL, REMOTE, PING, PONG, STOP

addrs = [('0.0.0.0', 12373), ('0.0.0.0', 12374)]
rpc = RPC(addrs[0], addrs)


for req_type, fd, data in rpc.run():
    if req_type == LOCAL:
        if data['callback'] == PING:
            for client_fd in rpc.hosts.keys():
                if rpc.fd_by_host[rpc.addrs[rpc.id]] != client_fd:
                    rpc.send_to_fd(client_fd, PING)
        elif data['callback'] == STOP:
            for client_fd in rpc.hosts.keys():
                rpc.send_to_fd(client_fd, STOP)
        else:
            print('local request', data)
    elif req_type == REMOTE:
        print('remote_request from {}'.format(fd), data)
        if data['callback'] == PING:
            time.sleep(1)
            rpc.send_to_fd(rpc.fd_by_host[tuple(data['host'])], PONG)
            print('ping')
        if data['callback'] == PONG:
            time.sleep(1)
            print('pong')
            rpc.send_to_fd(rpc.fd_by_host[tuple(data['host'])], PING)

