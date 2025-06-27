

FROM python

RUN apt update && apt upgrade -y

# Salin semua isi source code ke dalam folder kerja
COPY . /Ultra-Forward-Bot
WORKDIR /Ultra-Forward-Bot

# Install dependensi
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

# Jalankan start.sh
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8080
CMD ["/bin/bash", "/start.sh"]
