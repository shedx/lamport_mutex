import json


def serialize(**kwargs):
    return json.dumps(kwargs).encode('utf-8')


def deserialize(bytes):
    return json.loads(bytes.decode('utf-8'))
