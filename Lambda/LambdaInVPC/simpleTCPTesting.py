def handler(event, context):
    """
    This function puts into data into redis/mencached/rds/DynamoDB
    """
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # unhash the below line to setup
    tcphost = 'www.amazon.com'
    tcpport = 443
    server_address = (tcphost, tcpport)
    sock.settimeout(2) #suggest you set timeout shorter than the Lambda timeout
    sock.connect(server_address)
    return "Testing is successful"