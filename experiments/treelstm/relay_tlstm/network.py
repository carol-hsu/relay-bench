import numpy as np
import tvm
from tvm import relay
from tvm.relay import op
from tvm.relay import create_executor, Module
from tvm.relay.backend.interpreter import TensorValue
from tvm.relay.prelude import Prelude
from tvm.relay.testing import add_nat_definitions
import aot
import collections

class OrderedSet(collections.MutableSet):

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self):
        key = self.last()
        self.discard(key)
        return key

    def last(self):
        return self.end[1][0]

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)

def initialize(param):
    ty = param.type_annotation
    shape = [int(i) for i in ty.shape]
    return np.random.normal(0, 1, shape).astype('float32')

def copy_var(v):
    return relay.Var(v.name_hint, v.type_annotation)

class Network:
    stack = []
    cnt = 0

    def __init__(self, *, name="f", **kwargs):
        name = f"{name}_{Network.cnt}"
        Network.cnt += 1
        if len(Network.stack) is not 0:
            mod = Network.stack[-1].mod
            p = Network.stack[-1].p
        else:
            mod = Module()
            p = Prelude(mod)
            add_nat_definitions(p)

        self.mod = mod
        self.p = p
        self.inputs = []
        self.weights = OrderedSet()
        self.sub_network = OrderedSet()
        self.f = relay.GlobalVar(name)
        self.recurse = relay.Var("recurse")
        self.use_recurse = False
        self.ret_type = None
        body = self.build(**kwargs)
        assert isinstance(body, relay.Expr)
        if self.use_recurse:
            inputs = [copy_var(v) for v in self.inputs]
            body = relay.Let(self.recurse, relay.Function(inputs, self.call_from_outside(*inputs)), body)
        self.mod[self.f] = relay.Function(self.inputs + self.all_weights(), body, self.ret_type)

    def build(self, **kwargs):
        Network.stack.append(self)
        try:
            return self.build_impl(**kwargs)
        finally:
            Network.stack.pop()

    def build_impl(self, *args):
        raise NotImplementedError

    def weight(self, w):
        assert isinstance(w, relay.Var)
        self.weights.add(w)
        return w

    def input(self, i):
        assert isinstance(i, relay.Var)
        self.inputs.append(i)
        return i

    def all_weights(self):
        return list(set(list(self.weights) + [w for n in self.sub_network for w in n.all_weights()]))

    def call_from_outside(self, *inputs):
        return self.f(*(list(inputs) + self.all_weights()))

    def __call__(self, *inputs):
        if self in Network.stack:
            self.use_recurse = True
            return self.recurse(*inputs)
        else:
            assert len(Network.stack) > 0
            assert Network.stack[-1].mod == self.mod
            assert Network.stack[-1].p == self.p
            Network.stack[-1].sub_network.add(self)
            return self.call_from_outside(*inputs)

    def interface_type(self):
        relay.transform.InferType()(self.mod)
        t = self.mod[self.f].checked_type
        return relay.FuncType(t.arg_types[:len(self.inputs)], t.ret_type, t.type_params, t.type_constraints)

    def get(self):
        weights = []
        for x in self.all_weights():
            ty = x.type_annotation
            assert isinstance(ty, relay.TensorType)
            assert ty.dtype == 'float32'
            shape = [int(i) for i in ty.shape]
            weight = relay.const(np.random.normal(0, 1, shape).astype('float32'))
            weights.append(weight)
        inputs = [copy_var(v) for v in self.inputs]
        return relay.Function(inputs, self.f(*inputs, *weights))
