import socket


class Server:
    def __init__(self, host):
        self._connections = []
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(host)
        self._socket.listen(0)

    def accept(self):
        conn, addr = self._socket.accept()
        self._connections.append(conn)
        return conn

    def accept_n(self, n):
        for _ in range(n):
            self.accept()
        return [conn.fileno() for conn in self._connections[-n:]]

    def close(self):
        self._socket.close()
