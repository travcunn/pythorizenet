import lxml

try:
    import hashlib
    make_md5 = hashlib.md5
except ImportError:
    import md5
    make_md5 = md5.new

def generate_hash(*args):
    """generate_hash(hash_key, trans_id, amount)"""
    m = make_md5()
    map(m.update, args)
    return m.digest().encode('hex').upper()
