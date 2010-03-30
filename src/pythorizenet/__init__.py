import lxml

try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5

def generate_hash(*args):
    """generate_hash(hash_key, trans_id, amount)"""
    m = md5()
    map(m.update, args)
    return m.hexdigest().upper()
