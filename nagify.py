import urllib2
import base64
import time
import daemon
from daemon import runner
import dbconn
import subprocess
import json
import os
import re
import ConfigParser
import sys

try:
  basePath = os.path.dirname(os.path.realpath(__file__))
  config = ConfigParser.ConfigParser()
  config.read(basePath + "/config.ini")
  notificationsCgi = config.get('nagify', 'notificationsCgi')
  username = config.get('nagify', 'username')
  password = config.get('nagify', 'password')
  filter_contact = config.get('nagify', 'filter_contact')
  growlnotify_bin = config.get('notification-systems', 'growlnotify_bin')
  notifysend_bin = config.get('notification-systems', 'notifysend_bin')
  use = config.get('notification-systems', 'use')
  run_as_daemon = config.get('other', "run_as_daemon")
except Exception, e:
  print "Error reading config.ini"
  print e
  sys.exit(1)

filter_notification_command = "notify-service-by-email"
notificationsCgi = "%s?host=all&oldestfirst=on&jsonoutput" % notificationsCgi
authHeader = "Basic %s" % base64.encodestring('%s:%s' % (username, password)).replace('\n', '')

def getJsonObj():
  try:
    req = urllib2.Request(notificationsCgi)
    req.add_header("Authorization", authHeader)
    res = urllib2.urlopen(req)
    res = json.load(res)
    res = res["notifications"]["notifications"]
    res = filter(lambda x: x["contact"] == filter_contact, res)
    res = filter(lambda x: x["notification_command"] == filter_notification_command, res)
    return res
  except Exception, e:
    print Exception
    print e
    return False


def growlNotify(notifObj):
  """
    {
      u'information': u'OK - Slave is 1 seconds behind master',
      u'service': u'Mysql Slave lag',
      u'time': u'2013-05-02 03:15:53',
      u'host': u'mysql-g01-slave003199-eu.vpn',
      u'contact': u'eodabas',
      u'notification_command': u'notify-service-by-email',
      u'type': u'OK'
    }
  """
  try:
    myType = re.sub(r'.*\(([^\)]*)\)', r'\1', notifObj["type"])
    cmd = "%s --image \"%s\" -n nagios -t \"%s\" -m \"%s\" -s" % (
    growlnotify_bin,
    basePath + "/images/" + myType + ".png",
    notifObj["information"],
    "Service: " + notifObj["service"] + "\nHost: " + notifObj["host"] + "\nDate: " + notifObj["time"]
    )

    subprocess.check_call(cmd, shell=True)
    return True
  except Exception, e:
    print Exception
    print e
    return False

def notifySend(notifObj):
  """
    {
      u'information': u'OK - Slave is 1 seconds behind master',
      u'service': u'Mysql Slave lag',
      u'time': u'2013-05-02 03:15:53',
      u'host': u'mysql-g01-slave003199-eu.vpn',
      u'contact': u'eodabas',
      u'notification_command': u'notify-service-by-email',
      u'type': u'OK'
    }
  """
  try:
    myType = re.sub(r'.*\(([^\)]*)\)', r'\1', notifObj["type"])
    cmd = "%s -i \"%s\" -c nagios \"%s\" \"%s\"" % (
    notifysend_bin,
    basePath + "/images/" + myType + ".png",
    notifObj["information"],
    "Service: " + notifObj["service"] + "\nHost: " + notifObj["host"] + "\nDate: " + notifObj["time"]
    )

    subprocess.check_call(cmd, shell=True)
    return True
  except Exception, e:
    print Exception
    print e
    return False


def AppRun():
    try:
      dbconn.connectDb()
      while True:
        notifications = getJsonObj()
        if notifications != False:
          for notifObj in notifications:
            if not dbconn.checkNotification(notifObj):

              if use == "growl":
                notifRes = growlNotify(notifObj)
              elif use == "libnotify":
                notifRes = notifySend(notifObj)
              else:
                print "Unkown notification system: " + use
                sys.exit(1)

              if notifRes:
                dbconn.insertNotification(notifObj)
        time.sleep(10)
    except Exception, e:
      print Exception
      print e
      sys.exit(1)


class App():
  def __init__(self):
    self.stdin_path = '/dev/null'
    self.stdout_path = basePath + "/_stdout"
    self.stderr_path = basePath + "/_stderr"
    self.pidfile_path = basePath + "/_nagify.pid"
    self.pidfile_timeout = 5
  def run(self):
    AppRun()

if __name__ == "__main__":
  if run_as_daemon == "yes":
    daemon_runner = runner.DaemonRunner(App())
    daemon_runner.do_action()
  else:
    AppRun()
