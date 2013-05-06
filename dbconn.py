import sqlite3
import os


def connectDb():
  try:
    global conn
    conn = sqlite3.connect(os.path.dirname(os.path.realpath(__file__)) + "/history.db")
    c = conn.cursor()
    c.execute("""
              CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                information TEXT,
                time DATETIME,
                host VARCHAR(255),
                type VARCHAR(16)
                )
              """)
    c.execute("CREATE INDEX IF NOT EXISTS time_idx ON history (time)")
    c.execute("CREATE INDEX IF NOT EXISTS host_idx ON history (host)")
    c.execute("CREATE INDEX IF NOT EXISTS type_idx ON history (type)")
    conn.commit()
    return conn
  except Exception, e:
    print e
    return False
 
def insertNotification(notifObj):
  try:
    c = conn.cursor()
    c.execute("INSERT INTO history (information, time, host, type) VALUES ('%s', '%s', '%s', '%s')" % (
    notifObj["information"],
    notifObj["time"],
    notifObj["host"],
    notifObj["type"]
    ))
    conn.commit()
    return True
  except Exception, e:
    print e
    return False

def checkNotification(notifObj):
  try:
    c = conn.cursor()
    c.execute("SELECT count(id) FROM history WHERE time = '%s' AND host = '%s' AND type = '%s'" % (
    notifObj["time"],
    notifObj["host"],
    notifObj["type"]
    ))
    count = c.fetchone()[0]
    if count > 0:
      return True
    else:
      return False
  except Exception, e:
    print e
    return False


