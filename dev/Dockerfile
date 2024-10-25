# Use the latest Ubuntu image as the base
FROM ubuntu:latest

RUN apt-get update && \
  apt-get install -y vsftpd openssh-server supervisor && \
  rm -rf /var/lib/apt/lists/*

RUN useradd -m agile-badger && echo 'agile-badger:6Hv9]3kJt!^' | chpasswd
RUN useradd -m wise-fox && echo 'wise-fox:9Jp*2Lv@4zQ' | chpasswd

RUN echo "listen=YES" > /etc/vsftpd.conf && \
  echo "anonymous_enable=NO" >> /etc/vsftpd.conf && \
  echo "local_enable=YES" >> /etc/vsftpd.conf && \
  echo "write_enable=YES" >> /etc/vsftpd.conf && \
  echo "chroot_local_user=YES" >> /etc/vsftpd.conf && \
  echo "allow_writeable_chroot=YES" >> /etc/vsftpd.conf

RUN mkdir /var/run/sshd

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p /home/agile-badger/files && \
  chown agile-badger:agile-badger /home/agile-badger/files && \
  chmod 755 /home/agile-badger/files

RUN mkdir -p /home/wise-fox/files && \
  chown wise-fox:wise-fox /home/wise-fox/files && \
  chmod 755 /home/wise-fox/files


EXPOSE 21 22

CMD ["/usr/bin/supervisord"]
