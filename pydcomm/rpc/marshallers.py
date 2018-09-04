import cbor
import numpy as np

def nparray_marshal(x):
    return cbor.dumps((x.shape, list(x.flatten())))


def nparray_unmarshal(x):
    y = cbor.loads(x)
    return np.array(y[1]).reshape(y[0])
