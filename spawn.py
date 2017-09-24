import argparse

from lamport.lamport import Lamport
from rpc.rpc import RPC


if __name__ =='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', '-i', type=str, help='ip of current host', default='0.0.0.0')
    parser.add_argument('--port', '-p', type=int, help='port of current host')
    parser.add_argument('--mutex-file', '-m', type=str, help='path to mutex file', default='mutex.txt')
    parser.add_argument('--addrs', '-a', nargs='+', help='specify all addrs in format ip1:port1 ip2:port2 ...')

    args = parser.parse_args()

    addrs = list(map(lambda a: (a.split(':')[0], int(a.split(':')[1])), args.addrs))

    rpc = RPC((args.ip, args.port), addrs)
    lamport = Lamport(rpc, args.mutex_file)
    lamport.run()
