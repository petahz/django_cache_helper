import unicodedata
from hashlib import sha256

# List of Control Characters not useable by memcached
CONTROL_CHARACTERS = set([chr(i) for i in range(0, 33)])
CONTROL_CHARACTERS.add(chr(127))


def sanitize_key(key, max_length=250):
    """
    Truncates key to keep it under memcached char limit.  Replaces with hash.
    Remove control characters b/c of memcached restriction on control chars.
    """
    key = ''.join([c for c in key if c not in CONTROL_CHARACTERS])
    if len(key) > max_length:
        the_hash = sha256(key).hexdigest()
        key = key[:max_length - 64] + '-' + the_hash
    return key


def _sanitize_args(args, kwargs):
    """
    Creates unicode key from all kwargs/args
    """
    key = ""
    if args:
        key += get_normalized_term(args)
    if kwargs:
        key += get_normalized_term(kwargs)
    return key


def _func_type(func):
    argnames = func.func_code.co_varnames[:func.func_code.co_argcount]
    if len(argnames) > 0:
        if argnames[0] == 'self':
            return 'method'
        elif argnames[0] == 'cls':
            return 'class_method'
    return 'function'


def get_normalized_term(term, dash_replacement=''):
    term = str(term)
    term = term.decode('utf-8')
    term = term.lower()
    term = unicodedata.normalize('NFKD', unicode(term))\
        .encode('utf-8', 'ignore')
    term = term.strip()
    return term


def _func_info(func, args):
    func_type = _func_type(func)
    lineno = ":%s" % func.func_code.co_firstlineno

    if func_type == 'function':
        name = ".".join([func.__module__, func.__name__]) + lineno
        return name, args
    elif func_type == 'class_method':
        class_name = args[0].__name__
    else:
        class_name = args[0].__class__.__name__
    name = ".".join([func.__module__, class_name, func.__name__]) + lineno
    return name, args


def _cache_key(func_name, func_type, args, kwargs):
    if func_type in ['method', 'function']:
        args_string = _sanitize_args(args, kwargs)
    elif func_type == 'class_method':
        args_string = _sanitize_args(args[1:], kwargs)
    key = '%s%s' % (func_name, args_string)
    return key