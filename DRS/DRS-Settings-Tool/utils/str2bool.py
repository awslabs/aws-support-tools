#Convert string of "true" or "false" to boolean
def str2bool(string): 
    # ('true') is a plain string, not a tuple, so "in" would do a substring
    # match ("", "t", "rue" all counted as true). Compare exactly instead.
    value = string.strip().lower()
    if value == 'true':
        return True
    elif value == 'false':
        return False
