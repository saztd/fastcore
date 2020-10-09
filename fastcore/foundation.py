# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_foundation.ipynb (unless otherwise specified).

__all__ = ['defaults', 'copy_func', 'patch_to', 'patch', 'patch_property', 'add_docs', 'docs', 'custom_dir', 'arg0',
           'arg1', 'arg2', 'arg3', 'arg4', 'coll_repr', 'is_bool', 'mask2idxs', 'cycle', 'zip_cycle', 'is_indexer',
           'negate_func', 'GetAttr', 'delegate_attr', 'bind', 'argwhere', 'map_ex', 'filter_ex', 'range_of',
           'sorted_ex', 'listable_types', 'renumerate', 'first', 'nested_attr', 'stop', 'tst', 'tst2', 'CollBase', 'L',
           'save_config_file', 'read_config_file', 'Config']

# Cell
from .imports import *
from functools import lru_cache
from contextlib import contextmanager
from copy import copy
from configparser import ConfigParser
import random,pickle

# Cell
defaults = SimpleNamespace()

# Cell
def copy_func(f):
    "Copy a non-builtin function (NB `copy.copy` does not work for this)"
    if not isinstance(f,FunctionType): return copy(f)
    fn = FunctionType(f.__code__, f.__globals__, f.__name__, f.__defaults__, f.__closure__)
    fn.__dict__.update(f.__dict__)
    return fn

# Cell
def patch_to(cls, as_prop=False, cls_method=False):
    "Decorator: add `f` to `cls`"
    if not isinstance(cls, (tuple,list)): cls=(cls,)
    def _inner(f):
        for c_ in cls:
            nf = copy_func(f)
            # `functools.update_wrapper` when passing patched function to `Pipeline`, so we do it manually
            for o in functools.WRAPPER_ASSIGNMENTS: setattr(nf, o, getattr(f,o))
            nf.__qualname__ = f"{c_.__name__}.{f.__name__}"
            if cls_method:
                setattr(c_, f.__name__, MethodType(nf, c_))
            else:
                setattr(c_, f.__name__, property(nf) if as_prop else nf)
        return f
    return _inner

# Cell
def patch(f=None, *, as_prop=False, cls_method=False):
    "Decorator: add `f` to the first parameter's class (based on f's type annotations)"
    if f is None: return partial(patch, as_prop=as_prop, cls_method=cls_method)
    cls = next(iter(f.__annotations__.values()))
    return patch_to(cls, as_prop=as_prop, cls_method=cls_method)(f)

# Cell
def patch_property(f):
    "Deprecated; use `patch(as_prop=True)` instead"
    warnings.warn("`patch_property` is deprecated and will be removed; use `patch(as_prop=True)` instead")
    cls = next(iter(f.__annotations__.values()))
    return patch_to(cls, as_prop=True)(f)

# Cell
def add_docs(cls, cls_doc=None, **docs):
    "Copy values from `docs` to `cls` docstrings, and confirm all public methods are documented"
    if cls_doc is not None: cls.__doc__ = cls_doc
    for k,v in docs.items():
        f = getattr(cls,k)
        if hasattr(f,'__func__'): f = f.__func__ # required for class methods
        f.__doc__ = v
    # List of public callables without docstring
    nodoc = [c for n,c in vars(cls).items() if callable(c)
             and not n.startswith('_') and c.__doc__ is None]
    assert not nodoc, f"Missing docs: {nodoc}"
    assert cls.__doc__ is not None, f"Missing class docs: {cls}"

# Cell
def docs(cls):
    "Decorator version of `add_docs`, using `_docs` dict"
    add_docs(cls, **cls._docs)
    return cls

# Cell
def custom_dir(c, add:list):
    "Implement custom `__dir__`, adding `add` to `cls`"
    return dir(type(c)) + list(c.__dict__.keys()) + add

# Cell
class _Arg:
    def __init__(self,i): self.i = i
arg0 = _Arg(0)
arg1 = _Arg(1)
arg2 = _Arg(2)
arg3 = _Arg(3)
arg4 = _Arg(4)

# Cell
def coll_repr(c, max_n=10):
    "String repr of up to `max_n` items of (possibly lazy) collection `c`"
    return f'(#{len(c)}) [' + ','.join(itertools.islice(map(repr,c), max_n)) + (
        '...' if len(c)>10 else '') + ']'

# Cell
def is_bool(x):
    "Check whether `x` is a bool or None"
    return isinstance(x,(bool,NoneType)) or isinstance_str(x, 'bool_')

# Cell
def mask2idxs(mask):
    "Convert bool mask or index list to index `L`"
    if isinstance(mask,slice): return mask
    mask = list(mask)
    if len(mask)==0: return []
    it = mask[0]
    if hasattr(it,'item'): it = it.item()
    if is_bool(it): return [i for i,m in enumerate(mask) if m]
    return [int(i) for i in mask]

# Cell
def _is_array(x): return hasattr(x,'__array__') or hasattr(x,'iloc')

def _listify(o):
    if o is None: return []
    if isinstance(o, list): return o
    if isinstance(o, str) or _is_array(o): return [o]
    if is_iter(o): return list(o)
    return [o]

# Cell
def cycle(o):
    "Like `itertools.cycle` except creates list of `None`s if `o` is empty"
    o = _listify(o)
    return itertools.cycle(o) if o is not None and len(o) > 0 else itertools.cycle([None])

# Cell
def zip_cycle(x, *args):
    "Like `itertools.zip_longest` but `cycle`s through elements of all but first argument"
    return zip(x, *map(cycle,args))

# Cell
def is_indexer(idx):
    "Test whether `idx` will index a single item in a list"
    return isinstance(idx,int) or not getattr(idx,'ndim',1)

# Cell
def negate_func(f):
    "Create new function that negates result of `f`"
    def _f(*args, **kwargs): return not f(*args, **kwargs)
    return _f

# Cell
class GetAttr:
    "Inherit from this to have all attr accesses in `self._xtra` passed down to `self.default`"
    _default='default'
    def _component_attr_filter(self,k):
        if k.startswith('__') or k in ('_xtra',self._default): return False
        xtra = getattr(self,'_xtra',None)
        return xtra is None or k in xtra
    def _dir(self): return [k for k in dir(getattr(self,self._default)) if self._component_attr_filter(k)]
    def __getattr__(self,k):
        if self._component_attr_filter(k):
            attr = getattr(self,self._default,None)
            if attr is not None: return getattr(attr,k)
        raise AttributeError(k)
    def __dir__(self): return custom_dir(self,self._dir())
#     def __getstate__(self): return self.__dict__
    def __setstate__(self,data): self.__dict__.update(data)

# Cell
def delegate_attr(self, k, to):
    "Use in `__getattr__` to delegate to attr `to` without inheriting from `GetAttr`"
    if k.startswith('_') or k==to: raise AttributeError(k)
    try: return getattr(getattr(self,to), k)
    except AttributeError: raise AttributeError(k) from None

# Cell
class bind:
    "Same as `partial`, except you can use `arg0` `arg1` etc param placeholders"
    def __init__(self, fn, *pargs, **pkwargs):
        self.fn,self.pargs,self.pkwargs = fn,pargs,pkwargs
        self.maxi = max((x.i for x in pargs if isinstance(x, _Arg)), default=-1)

    def __call__(self, *args, **kwargs):
        args = list(args)
        kwargs = {**self.pkwargs,**kwargs}
        for k,v in kwargs.items():
            if isinstance(v,_Arg): kwargs[k] = args.pop(v.i)
        fargs = [args[x.i] if isinstance(x, _Arg) else x for x in self.pargs] + args[self.maxi+1:]
        return self.fn(*fargs, **kwargs)

# Cell
def argwhere(iterable, f, negate=False, **kwargs):
    "Like `filter_ex`, but return indices for matching items"
    if kwargs: f = partial(f,**kwargs)
    if negate: f = negate_func(f)
    return [i for i,o in enumerate(iterable) if f(o)]

# Cell
def map_ex(iterable, f, *args, gen=False, **kwargs):
    "Like `map`, but use `bind`, and supports `str` and indexing"
    g = (bind(f,*args,**kwargs) if callable(f)
         else f.format if isinstance(f,str)
         else f.__getitem__)
    res = map(g, iterable)
    if gen: return res
    return list(res)

# Cell
def filter_ex(iterable, f=noop, negate=False, gen=False, **kwargs):
    "Like `filter`, but passing `kwargs` to `f`, defaulting `f` to `noop`, and adding `negate` and `gen`"
    if kwargs: f = partial(f,**kwargs)
    if negate: f = negate_func(f)
    res = filter(f, iterable)
    if gen: return res
    return list(res)

# Cell
def range_of(a, b=None, step=None):
    "All indices of collection `a`, if `a` is a collection, otherwise `range`"
    if is_coll(a): a = len(a)
    return list(range(a,b,step) if step is not None else range(a,b) if b is not None else range(a))

# Cell
def sorted_ex(iterable, key=None, reverse=False):
    "Like `sorted`, but if key is str use `attrgetter`; if int use `itemgetter`"
    if isinstance(key,str):   k=lambda o:getattr(o,key,0)
    elif isinstance(key,int): k=itemgetter(key)
    else: k=key
    return sorted(iterable, key=k, reverse=reverse)

# Cell
listable_types = typing.Collection,Generator,map,filter,zip

# Cell
def renumerate(iterable, start=0):
    "Same as `enumerate`, but returns index as 2nd element instead of 1st"
    return ((o,i) for i,o in enumerate(iterable, start=start))

# Cell
def first(x):
    "First element of `x`, or None if missing"
    try: return next(iter(x))
    except StopIteration: return None

# Cell
def nested_attr(o, attr, default=None):
    "Same as `getattr`, but if `attr` includes a `.`, then looks inside nested objects"
    try:
        for a in attr.split("."): o = getattr(o, a)
    except AttributeError: return default
    return o

# Cell
def stop(e=StopIteration):
    "Raises exception `e` (by default `StopException`)"
    raise e

def tst():
    try:
        stop()
    except StopIteration:
        return True

def tst2():
    try:
        stop(e=ValueError)
    except ValueError:
        return True

# Cell
class CollBase:
    "Base class for composing a list of `items`"
    def __init__(self, items): self.items = items
    def __len__(self): return len(self.items)
    def __getitem__(self, k): return self.items[list(k) if isinstance(k,CollBase) else k]
    def __setitem__(self, k, v): self.items[list(k) if isinstance(k,CollBase) else k] = v
    def __delitem__(self, i): del(self.items[i])
    def __repr__(self): return self.items.__repr__()
    def __iter__(self): return self.items.__iter__()

# Cell
class _L_Meta(type):
    def __call__(cls, x=None, *args, **kwargs):
        if not args and not kwargs and x is not None and isinstance(x,cls): return x
        return super().__call__(x, *args, **kwargs)

# Cell
class L(GetAttr, CollBase, metaclass=_L_Meta):
    "Behaves like a list of `items` but can also index with list of indices or masks"
    _default='items'
    def __init__(self, items=None, *rest, use_list=False, match=None):
        if rest: items = (items,)+rest
        if items is None: items = []
        if (use_list is not None) or not _is_array(items):
            items = list(items) if use_list else _listify(items)
        if match is not None:
            if is_coll(match): match = len(match)
            if len(items)==1: items = items*match
            else: assert len(items)==match, 'Match length mismatch'
        super().__init__(items)

    @property
    def _xtra(self): return None
    def _new(self, items, *args, **kwargs): return type(self)(items, *args, use_list=None, **kwargs)
    def __getitem__(self, idx): return self._get(idx) if is_indexer(idx) else L(self._get(idx), use_list=None)
    def copy(self): return self._new(self.items.copy())

    def _get(self, i):
        if is_indexer(i) or isinstance(i,slice): return getattr(self.items,'iloc',self.items)[i]
        i = mask2idxs(i)
        return (self.items.iloc[list(i)] if hasattr(self.items,'iloc')
                else self.items.__array__()[(i,)] if hasattr(self.items,'__array__')
                else [self.items[i_] for i_ in i])

    def __setitem__(self, idx, o):
        "Set `idx` (can be list of indices, or mask, or int) items to `o` (which is broadcast if not iterable)"
        if isinstance(idx, int): self.items[idx] = o
        else:
            idx = idx if isinstance(idx,L) else _listify(idx)
            if not is_iter(o): o = [o]*len(idx)
            for i,o_ in zip(idx,o): self.items[i] = o_

    def __eq__(self,b):
        if isinstance_str(b, 'ndarray'): return array_equal(b, self)
        if isinstance(b, (str,dict)): return False
        return all_equal(b,self)

    def sorted(self, key=None, reverse=False): return self._new(sorted_ex(self, key=key, reverse=reverse))
    def __iter__(self): return iter(self.items.itertuples() if hasattr(self.items,'iloc') else self.items)
    def __contains__(self,b): return b in self.items
    def __reversed__(self): return self._new(reversed(self.items))
    def __invert__(self): return self._new(not i for i in self)
    def __repr__(self): return repr(self.items) if _is_array(self.items) else coll_repr(self)
    def __mul__ (a,b): return a._new(a.items*b)
    def __add__ (a,b): return a._new(a.items+_listify(b))
    def __radd__(a,b): return a._new(b)+a
    def __addi__(a,b):
        a.items += list(b)
        return a

    @classmethod
    def split(cls, s, sep=None, maxsplit=-1): return cls(s.split(sep,maxsplit))
    @classmethod
    def range(cls, a, b=None, step=None): return cls(range_of(a, b=b, step=step))

    def map(self, f, *args, gen=False, **kwargs): return self._new(map_ex(self, f, *args, gen=gen, **kwargs))
    def argwhere(self, f, negate=False, **kwargs): return self._new(argwhere(self, f, negate, **kwargs))
    def filter(self, f=noop, negate=False, gen=False, **kwargs):
        return self._new(filter_ex(self, f=f, negate=negate, gen=gen, **kwargs))

    def unique(self): return L(dict.fromkeys(self).keys())
    def enumerate(self): return L(enumerate(self))
    def renumerate(self): return L(renumerate(self))
    def val2idx(self): return {v:k for k,v in self.enumerate()}
    def itemgot(self, *idxs):
        x = self
        for idx in idxs: x = x.map(itemgetter(idx))
        return x

    def attrgot(self, k, default=None):
        return self.map(lambda o: o.get(k,default) if isinstance(o, dict) else nested_attr(o,k,default))
    def cycle(self): return cycle(self)
    def map_dict(self, f=noop, *args, gen=False, **kwargs): return {k:f(k, *args,**kwargs) for k in self}
    def map_filter(self, f=noop, g=noop, *args, gen=False, **kwargs):
        res = filter(g, self.map(f, *args, gen=gen, **kwargs))
        if gen: return res
        return self._new(res)
    def map_first(self, f=noop, g=noop, *args, **kwargs):
        return first(self.map_filter(f, g, *args, gen=False, **kwargs))

    def starmap(self, f, *args, **kwargs): return self._new(itertools.starmap(partial(f,*args,**kwargs), self))
    def zip(self, cycled=False): return self._new((zip_cycle if cycled else zip)(*self))
    def zipwith(self, *rest, cycled=False): return self._new([self, *rest]).zip(cycled=cycled)
    def map_zip(self, f, *args, cycled=False, **kwargs): return self.zip(cycled=cycled).starmap(f, *args, **kwargs)
    def map_zipwith(self, f, *rest, cycled=False, **kwargs):
        return self.zipwith(*rest, cycled=cycled).starmap(f, **kwargs)
    def shuffle(self):
        it = copy(self.items)
        random.shuffle(it)
        return self._new(it)

    def concat(self): return self._new(itertools.chain.from_iterable(self.map(L)))
    def reduce(self, f, initial=None): return reduce(f, self) if initial is None else reduce(f, self, initial)
    def sum(self): return self.reduce(operator.add)
    def product(self): return self.reduce(operator.mul)
    def setattrs(self, attr, val): [setattr(o,attr,val) for o in self]

# Cell
add_docs(L,
         __getitem__="Retrieve `idx` (can be list of indices, or mask, or int) items",
         range="Class Method: Same as `range`, but returns `L`. Can pass collection for `a`, to use `len(a)`",
         split="Class Method: Same as `str.split`, but returns an `L`",
         copy="Same as `list.copy`, but returns an `L`",
         sorted="New `L` sorted by `key`. If key is str use `attrgetter`; if int use `itemgetter`",
         unique="Unique items, in stable order",
         val2idx="Dict from value to index",
         filter="Create new `L` filtered by predicate `f`, passing `args` and `kwargs` to `f`",
         argwhere="Like `filter`, but return indices for matching items",
         map="Create new `L` with `f` applied to all `items`, passing `args` and `kwargs` to `f`",
         map_filter="Same as `map` with `f` followed by `filter` with `g`",
         map_first="First element of `map_filter`",
         map_dict="Like `map`, but creates a dict from `items` to function results",
         starmap="Like `map`, but use `itertools.starmap`",
         itemgot="Create new `L` with item `idx` of all `items`",
         attrgot="Create new `L` with attr `k` (or value `k` for dicts) of all `items`.",
         cycle="Same as `itertools.cycle`",
         enumerate="Same as `enumerate`",
         renumerate="Same as `renumerate`",
         zip="Create new `L` with `zip(*items)`",
         zipwith="Create new `L` with `self` zip with each of `*rest`",
         map_zip="Combine `zip` and `starmap`",
         map_zipwith="Combine `zipwith` and `starmap`",
         concat="Concatenate all elements of list",
         shuffle="Same as `random.shuffle`, but not inplace",
         reduce="Wrapper for `functools.reduce`",
         sum="Sum of the items",
         product="Product of the items",
         setattrs="Call `setattr` on all items"
        )

# Cell
#hide
L.__signature__ = pickle.loads(b'\x80\x03cinspect\nSignature\nq\x00(cinspect\nParameter\nq\x01X\x05\x00\x00\x00itemsq\x02cinspect\n_ParameterKind\nq\x03K\x01\x85q\x04Rq\x05\x86q\x06Rq\x07}q\x08(X\x08\x00\x00\x00_defaultq\tNX\x0b\x00\x00\x00_annotationq\ncinspect\n_empty\nq\x0bubh\x01X\x04\x00\x00\x00restq\x0ch\x03K\x02\x85q\rRq\x0e\x86q\x0fRq\x10}q\x11(h\th\x0bh\nh\x0bubh\x01X\x08\x00\x00\x00use_listq\x12h\x03K\x03\x85q\x13Rq\x14\x86q\x15Rq\x16}q\x17(h\t\x89h\nh\x0bubh\x01X\x05\x00\x00\x00matchq\x18h\x14\x86q\x19Rq\x1a}q\x1b(h\tNh\nh\x0bubtq\x1c\x85q\x1dRq\x1e}q\x1fX\x12\x00\x00\x00_return_annotationq h\x0bsb.')

# Cell
Sequence.register(L);

# Cell
def save_config_file(file, d):
    "Write settings dict to a new config file, or overwrite the existing one."
    config = ConfigParser()
    config['DEFAULT'] = d
    config.write(open(file, 'w'))

# Cell
def read_config_file(file):
    config = ConfigParser()
    config.read(file)
    return config

# Cell
def _add_new_defaults(cfg, file, **kwargs):
    for k,v in kwargs.items():
        if cfg.get(k, None) is None:
            cfg[k] = v
            save_config_file(file, cfg)

# Cell
@lru_cache(maxsize=None)
class Config:
    "Reading and writing `settings.ini`"
    def __init__(self, cfg_name='settings.ini'):
        cfg_path = Path.cwd()
        while cfg_path != cfg_path.parent and not (cfg_path/cfg_name).exists(): cfg_path = cfg_path.parent
        self.config_file = cfg_path/cfg_name
        assert self.config_file.exists(), f"Could not find {cfg_name}"
        self.d = read_config_file(self.config_file)['DEFAULT']
        _add_new_defaults(self.d, self.config_file,
                         host="github", doc_host="https://%(user)s.github.io", doc_baseurl="/%(lib_name)s/")

    def __setitem__(self,k,v): self.d[k] = str(v)
    def __contains__(self,k):  return k in self.d
    def save(self):            save_config_file(self.config_file,self.d)
    def __getattr__(self,k):   return stop(AttributeError(k)) if k=='d' or k not in self.d else self.get(k)

    def get(self,k,default=None):
        v = self.d.get(k, default)
        if v is None: return v
        return self.config_file.parent/v if k.endswith('_path') else v