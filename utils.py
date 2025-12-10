def stringify_ids(obj):
    """
    Recursively convert all *_id fields in a dict or list to strings.
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if v is None:
                out[k] = None
            elif (k.endswith("_id")) and isinstance(v, (int,)):
                out[k] = str(v)
            else:
                out[k] = stringify_ids(v)
        return out
    if isinstance(obj, list):
        return [stringify_ids(i) for i in obj]
    return obj
