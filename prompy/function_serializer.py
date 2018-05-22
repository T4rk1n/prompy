import marshal
import types
import ctypes

from typing import NamedTuple


class SerializedFunction(NamedTuple):
    code: bytes
    argsdef: bytes
    closure: bytes
    name: str


def serialize_closure(closure):
    if not closure:
        return
    c = []
    for cell in closure:
        c.append(cell.cell_contents)
    return marshal.dumps(tuple(c))


def deserialize_closure(closure):
    if not closure:
        return
    c = marshal.loads(closure)
    fun = (lambda *args: lambda: args)(*c)
    return fun.__closure__


def serialize_fun(fun):
    code = marshal.dumps(fun.__code__)
    argsdef = marshal.dumps(fun.__defaults__)
    closure = serialize_closure(fun.__closure__)
    return SerializedFunction(code, argsdef, closure, fun.__name__)


def deserialize_fun(fun: SerializedFunction, namespace=None):
    ns = namespace or {}
    namespace = dict(**ns, **globals())  # add global otherwise no access to builtins.
    code = marshal.loads(fun.code)
    argsdef = marshal.loads(fun.argsdef)
    closure = deserialize_closure(fun.closure)
    return types.FunctionType(code, namespace, fun.name, argsdef, closure)

