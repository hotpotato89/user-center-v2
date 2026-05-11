import logging

_logging_configured = False

def setup_logging():
    global _logging_configured
    if _logging_configured:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    _logging_configured = True

def get_logger(name: str):
    setup_logging()
    return logging.getLogger(name)