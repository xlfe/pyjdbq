
## pyjdbq

## Python journald to Google Big Query remote logger

### Installation


Create a Big Query table using schema.txt (default is to use the database "logs" and table "pyjdbq")

These installation instructions should work on CentOS/RHEL

Prepare the system by installing dependencies and creating a pyjdbq user
with home directory /opt/pyjdbq and adding them to the systemd-journal group
(which means they can read all journald entries)

```bash
sudo dnf install python-systemd unzip
sudo useradd -d /opt/pyjdbq -G systemd-journal -m -s /sbin/nologin pyjdbq
sudo -u pyjdbq pip install google-api-python-client pytz tzlocal -t /opt/pyjdbq/
```

Download pyjdbq and move it into /opt/pyjdbq
Put your JSON Google Big Query service account credentials.json file into the same directory

```bash

curl -LOk https://github.com/xlfe/pyjdbq/archive/master.zip
unzip master.zip
sudo cp pyjdbq-master/* /opt/pyjdbq
sudo mv credentials.json /opt/pyjdbq
sudo chown -R pyjdbq: /opt/pyjdbq
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

Install the systemd unit file and check your journald logs to make sure there's no errors

```bash

sudo mv /opt/pyjdbq/pyjdbq.service /etc/systemd/system/
sudo systemctl enable pyjdbq
sudo systemctl start pyjdbq; sudo journalctl -f
```



