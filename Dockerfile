FROM python:3.7

RUN pip install python-telegram-bot
ADD medinabot.py /

CMD ["python","medinabot.py"]