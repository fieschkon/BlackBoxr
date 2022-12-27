# Get first item in iterable
from datetime import datetime
import logging
import os
import platform
import random
import string
import subprocess
from PySide6.QtCore import QPointF
from dictdiffer import diff, patch, swap, revert


def first(iterable, default=None):
  for item in iterable:
    return item
  return default

def makeDir(path):
  try:
    os.makedirs(path)
  except FileExistsError:
   pass

def getDuration(then, now = datetime.now(), interval = "default"):

    # Returns a duration as specified by variable interval
    # Functions, except totalDuration, returns [quotient, remainder]

    duration = now - then # For build-in functions
    duration_in_s = duration.total_seconds() 
    
    def years():
      return divmod(duration_in_s, 31536000) # Seconds in a year=31536000.

    def days(seconds = None):
      return divmod(seconds if seconds != None else duration_in_s, 86400) # Seconds in a day = 86400

    def hours(seconds = None):
      return divmod(seconds if seconds != None else duration_in_s, 3600) # Seconds in an hour = 3600

    def minutes(seconds = None):
      return divmod(seconds if seconds != None else duration_in_s, 60) # Seconds in a minute = 60

    def seconds(seconds = None):
      if seconds != None:
        return divmod(seconds, 1)   
      return duration_in_s

    def totalDuration():
        y = years()
        d = days(y[1]) # Use remainder to calculate next variable
        h = hours(d[1])
        m = minutes(h[1])
        s = seconds(m[1])

        return "Time between dates: {} years, {} days, {} hours, {} minutes and {} seconds".format(int(y[0]), int(d[0]), int(h[0]), int(m[0]), int(s[0]))

    return {
        'years': int(years()[0]),
        'days': int(days()[0]),
        'hours': int(hours()[0]),
        'minutes': int(minutes()[0]),
        'seconds': int(seconds()),
        'default': totalDuration()
    }

def searchFilesForUUID(files : list[str], uuid : str):
  print(f'Searching for {uuid}...')
  for file in files:
    if file.endswith('.json'):
      with open(file, 'r') as fp:
        # read all lines using readline()
        lines = fp.readlines()
        for row in lines:
            # check if string present on a current line
            searchterm = f'"uuid": "{uuid}"'
            #print(row.find(word))
            # find() method returns -1 if the value is not found,
            # if found it returns index of the first occurrence of the substring
            if row.find(searchterm) != -1:
              return file
  return False

def log(context, message):
  logger = logging.getLogger(context)
  logger.info(message)
  print(message)

def closestPoint(pointtosearch : QPointF, points : list[QPointF]):
  closest_point = None
  closest_dist = None
  for point in points:
      distance = ((point.x() - pointtosearch.x())**2 + (point.y() - pointtosearch.y())**2)**0.5
      if closest_dist is None or distance < closest_dist:
          closest_point = point
          closest_dist = distance
  return closest_point

def getTheme():
  match platform.system():
    case 'Darwin':
      cmd = 'defaults read -g AppleInterfaceStyle'
      p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, shell=True)
      return 'dark' if bool(p.communicate()[0]) else 'light'
    case 'Windows':
      try:
          import winreg
      except ImportError:
          return 'light'
      registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
      reg_keypath = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
      try:
          reg_key = winreg.OpenKey(registry, reg_keypath)
      except FileNotFoundError:
          return 'light'

      for i in range(1024):
          try:
              value_name, value, _ = winreg.EnumValue(reg_key, i)
              if value_name == 'AppsUseLightTheme':
                  return 'dark' if value == 0 else 'light'
          except OSError:
              break
      return 'light'

def randomString(length=5)->str:
  return ''.join(random.choices(string.ascii_letters, k=length))

def diffdict(dictA : dict, dictB : dict):
  return list(diff(dictA, dictB))