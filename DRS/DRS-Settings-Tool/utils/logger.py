import logging
import sys
import os

path = os.path.dirname(__file__).replace('\\utils', '')


def get_logger(name):
    log_format = '%(asctime)s  %(name)8s  %(levelname)5s  %(message)s'
    logging.basicConfig(level=logging.NOTSET,
                        format=log_format,
                        filename=path + '\\DRS-Update-Tool.log',
                        filemode='a')
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(log_format))
    logging.getLogger(name).addHandler(console)
    return logging.getLogger(name)

