import logging
import os.path
import time

def setup_logger(log_file, log_level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(log_level)
    log_path = os.path.dirname(os.path.abspath(log_file))
    os.makedirs(log_path, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

log_file_name = ""
app_logger = setup_logger("Logs/robot_{}.log".format(log_file_name))

def change_log_file(logger, new_log_file):
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            logger.removeHandler(handler)
    log_file_name = "Logs/robot_{}.log".format(new_log_file)
    return setup_logger(log_file_name, logger.getEffectiveLevel())

if __name__ == "__main__":
    log_file_name = "Logs/robot_log.log"
    app_logger = setup_logger(log_file_name)
    app_logger.debug('this is a logger debug message')
    app_logger.info('this is a logger info message')
    app_logger.warning('this is a logger warning message')
    app_logger.error('this is a logger error message')
    app_logger.critical('this is a logger critical message')
    print('Test')
