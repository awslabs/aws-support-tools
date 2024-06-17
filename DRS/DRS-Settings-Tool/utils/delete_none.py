##Delete None values recursively from all of the dictionaries, tuples, lists, sets
def delete_none(object):
    true = 'true'
    fales = 'false'
    null = None
    if isinstance(object, dict):
        for key, value in list(object.items()):
            if isinstance(value, (list, dict, tuple, set)):
                object[key] = delete_none(value)
            elif value in (None, '') or key in (None, ''):
                del object[key]

    elif isinstance(object, (list, set, tuple)):
        object = type(object)(delete_none(item) for item in object if item is not None)

    return object
