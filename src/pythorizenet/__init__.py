import md5

def generate_hash(*args):
    """generate_hash(hash_key, trans_id, amount)"""
    m = md5.new()
    map(m.update, args)
    return m.digest().encode('hex').upper()
