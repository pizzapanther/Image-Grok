#!/usr/bin/env python

import os
import socket
import subprocess

def run_gae ():
  mydir = os.path.dirname(__file__)
  basedir = os.path.join(mydir, '..')
  os.chdir(basedir)
  
  kwargs = {
    'host': socket.getfqdn(),
  }
  
  #--enable_sendmail
  cmd = "dev_appserver.py --host {host} --port 8080 --admin_host {host} --admin_port 8888 --storage_path tmp/ backend/".format(**kwargs)
  print(cmd)
  status = subprocess.call(cmd, shell=True)
  
if __name__ == "__main__":
  run_gae()
  