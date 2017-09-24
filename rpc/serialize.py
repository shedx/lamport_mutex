import json


def serialize(**kwargs):
    return json.dumps(kwargs).encode('utf-8') + b'\n'
    # add \n so there is no need to distinguish from console input


def deserialize(bytes):
    return json.loads(bytes.decode('utf-8'))
