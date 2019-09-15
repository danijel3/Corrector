import logging
from Corrector import app as application

if __name__ == "__main__":
    application.logger = logging.getLogger('s2t-corrector')
    application.run(debug=True)
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    application.logger.handlers = gunicorn_logger.handlers
    application.logger.setLevel(gunicorn_logger.level)
