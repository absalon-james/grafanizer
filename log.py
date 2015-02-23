import logging
logger = logging.getLogger('grafanizer')
logger.setLevel(logging.DEBUG)

file_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
file_formatter = logging.Formatter(file_format)
file_handler = logging.FileHandler('/var/log/grafanizer/grafanizer.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

stream_formatter = logging.Formatter('%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)
