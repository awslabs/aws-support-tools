#Convert string of "true" or "false" to boolean
def str2bool(string): 
    if string.lower() in ('true'):
        return True
    elif string.lower() in ('false'):
        return False
