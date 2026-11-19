import logging
import sys
import os

# Directory of the tool (the parent of this "utils" folder). Works on any OS.
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_logger(name):
    log_format = '%(asctime)s  %(name)8s  %(levelname)5s  %(message)s'
    # INFO instead of NOTSET, so DEBUG output from boto3/botocore (full API
    # requests and responses) isn't written to the log file.
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        filename=os.path.join(path, 'DRS-Update-Tool.log'),
                        filemode='a')
    logger = logging.getLogger(name)
    if not any(isinstance(h, logging.StreamHandler) and getattr(h, 'stream', None) is sys.stdout
               for h in logger.handlers):
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter(log_format))
        logger.addHandler(console)
    return logger
