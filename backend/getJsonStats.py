#!/usr/bin/python
import socket
import struct
import subprocess;
import os;
import time;
import json;

import sqlalchemy;
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from datetime import datetime

TOTAL_BYTES = {}
CURR_BYTES = {}
IP_ADDRESS = {}
tmp_file="file"
return_value = subprocess.call(["../backend/getRawStats.sh", tmp_file]);

file_name = "../my_config.cfg"

# Read config file
config = {};
config_file = open(file_name, 'r')
for line in config_file:
    # Get rid of \n
    line = line.rstrip()
    # Empty?
    if not line:
        continue
    # Comment?
    if line.startswith("#"):
        continue
    (name, value) = line.split("=")
    name = name.strip()
    config[name] = value

# DB Configuration
Base = declarative_base()
class Stats(Base):
        __tablename__ = 'stats'

        id = Column(Integer, primary_key=True)
        timestamp = Column(DateTime)
        data = Column(String);

# Connect to DB
e = create_engine('mysql+mysqldb://' + config['user'] + ':' + config['password'] + '@localhost/routerstats', pool_recycle=3600)
Session = sessionmaker(bind=e)
session = Session()

interval = 5;
index=0
key = ""
value = ""
with open(tmp_file) as f:
	for line in f:
		lineArray = line.split("=");
		if (len(lineArray) == 2):
			key = lineArray[0];
			value = lineArray[1]
		
		if line.startswith("["):
			index = index + 1
		if index < 1:
			if key == "interval":
				interval = value;
		else:
			if key == "currBytes":
				CURR_BYTES[index] = value
			if key == "ipAddress":
				try:
					IP_ADDRESS[index] = socket.inet_ntoa(struct.pack('!L',int(value)))
				except Exception:
					pass
			if key == "totalBytes":
				TOTAL_BYTES[index] = value;

def bytes_to_bitrate(bytes, interval = 5):
	return ((int(bytes) * 8 / 1000) / int(interval))

results = []
for x in range(1, index):
	result = {}
	try:
		result["address"] = IP_ADDRESS[x];
		result["current_bitrate"] = bytes_to_bitrate(CURR_BYTES[x], interval);
		results.append(result)
	except Exception:
		pass
output = {};
output["time"] = str(time.time()).split(".")[0];
output["results"] = results;
jsonElement = json.dumps(output);
print jsonElement

# Persist data to DB
date = datetime.now()
element = Stats(timestamp=date, data=jsonElement);
session.add(element);
session.commit();

# Delete tmp file
if os.path.isfile(tmp_file):
	os.remove(tmp_file);
