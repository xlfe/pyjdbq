
## pyjdbq

## Python journald to Google Big Query remote logger

### Installation


This should work on CentOS/RHEL

Prepare the system by installing dependencies and creating a pyjdbq user
with home directory /opt/pyjdbq and adding them to the systemd-journal group
(which means they can read all journald entries)

```bash
sudo yum install python-systemd
sudo useradd -d /opt/pyjdbq -G systemd-journal -m -s /sbin/nologin pyjdbq
```

Download pyjdbq and move it into /opt/pyjdbq

```bash

wget https://github.com/xlfe/pyjdbq/archive/master.zip
unzip master.zip
sudo cp pyjdbq-master/* /opt/pyjdbq

# Put your JSON Google Big Query service account credentials file into the same directory
sudo mv credentials.json /opt/pyjdbq

sudo chown -R pyjdbq: /opt/pyjdbq/*
```

Finally install the systemd script (you should edit it to set options)

Available options:

```bash
[user@server ~]$ python pyjdbq.py --help
usage: pyjdbq.py [-h] [--dataset DATASET] [--table TABLE] [--creds CREDS]
                 [--cursor CURSOR] [--count COUNT] [--timeout TIMEOUT]
                 [--debug]

pyjdbq (journald to big query)

stream journald logs into a biq query table

optional arguments:
  -h, --help         show this help message and exit
  --dataset DATASET  BigQuery dataset
  --table TABLE      BigQuery table
  --creds CREDS      JSON credentials file for BigQuery
  --cursor CURSOR    Full path to store the cursor file
  --count COUNT      Events to store before inserting
  --timeout TIMEOUT  Seconds to wait for COUNT logs before inserting anyway
  --debug            Extra verbose
```


