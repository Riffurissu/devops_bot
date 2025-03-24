FROM python:3.10-alpine
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 1001
CMD ["python", "bot.py"]
