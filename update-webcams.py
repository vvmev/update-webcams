#!/usr/bin/env python

import os
import sys
import tempfile
import time

from configparser import ConfigParser
from datetime import datetime
from ftplib import FTP
from shutil import copyfile
from subprocess import check_output, CalledProcessError
from urllib.error import URLError
from urllib.request import urlretrieve


class WebcamProcessor():
  def __init__(self, title, name, url, archive_dir=None, ext="jpg", ftp=None, label_pattern='%Y-%m-%d %H:%M Webcam {}'):
    self.archive_dir = archive_dir
    self.ext = ext
    self.ftp = ftp
    self.label_pattern = label_pattern
    self.name = name
    self.title = title
    self.url = url
    (fh, self.tmp) = tempfile.mkstemp(suffix="." + self.ext)
    os.close(fh)
    self.ts = datetime.now()

  def is_valid_file(self):
    try:
      return os.path.getsize(self.tmp) > 0
    except FileNotFoundError:
      return False

  def download(self):
    try:
      urlretrieve(self.url, self.tmp)
    except URLError as e:
      print(f"Unable to download {self.url}: {e}", file=sys.stderr)
      raise e

  def archive(self):
    if self.archive_dir and self.is_valid_file():
      yearmonth = self.ts.strftime("%Y-%m")
      day = self.ts.strftime("%Y-%m-%d")
      time = self.ts.strftime("%H-%M")
      target = f"{self.archive_dir}/{self.name}/{yearmonth}/{day}/{day}-{time}.{self.ext}"
      os.makedirs(os.path.dirname(target), exist_ok=True)
      copyfile(self.tmp, target)
    pass

  def paint(self):
    (fh, tmp) = tempfile.mkstemp(suffix="." + self.ext)
    os.close(fh)
    label = self.ts.strftime(self.label_pattern)
    label = label.replace("{}", self.title)

    cmd = ["gm", "convert", self.tmp, "-fill", "white", "-undercolor", "#00000080", "-gravity", "South",
           "-font", "Helvetica-Bold", "-pointsize", "18", "-draw", f"text 10,5 \"{label}\"", tmp]
    try:
      check_output(cmd)
      os.unlink(self.tmp)
      self.tmp = tmp
    except CalledProcessError as e:
      print(f"Unable to paint image {tmp}, gm exited with {e.returncode}")
      pass

  def upload(self):
    if self.ftp:
      with open(self.tmp, 'rb') as fd:
        self.ftp.storbinary(f"STOR {self.name}", fd)

  def finish(self):
    try:
      os.unlink(self.tmp)
    except FileNotFoundError:
      pass

  def process(self):
    try:
      self.download()
      self.archive()
      self.paint()
      self.upload()
    finally:
      self.finish()


def replacetoken(s, v):
  return s.replace('{}', v)

def get_ftp(g):
  if 'hostname' in g:
    return FTP(g['hostname'], g['username'], g['password'])


if __name__ == "__main__":
  ftp = None
  try:
    if len(sys.argv) > 1:
      configfile = sys.argv[1]
    else:
      configfile = "webcams.ini"
    if not os.path.exists(configfile):
      print(f"Unable to load {configfile}: file doesn't exist", file=sys.stderr)
    config = ConfigParser(interpolation = None)
    config.read(configfile)

    g = config['general']
    if 'hostname' in g and (not 'username' in g or not 'password' in g):
      print("Must have all three \"servername\", \"username\", and \"password\" to define FTP connection",
            file=sys.sterr)
      sys.exit(64)
    archive_dir = g.get('archive_dir', None)
    interval = g.getint('interval', 0)
    label_pattern = g.get('label_pattern', None)
    url_pattern = g.get('url_pattern', 'http://{}')
    verbose = g.getboolean('verbose', "false")

    while True:
      now = time.monotonic()
      ftp = get_ftp(g)
      for k in filter(lambda x: 'general' != x, config.sections()):
        try:
          cam = config[k]
          if 'url' in cam:
            url = cam['url']
          else:
            url = replacetoken(url_pattern, cam['host'])
          args = {}
          if archive_dir:
            args['archive_dir'] = archive_dir
          if 'ext' in cam:
            args['ext'] = cam['ext']
          args['ftp'] = ftp
          if label_pattern:
            args['label_pattern'] = label_pattern
          if verbose:
            print(f"Updating {cam['title']} from {url}")
          p = WebcamProcessor(cam['title'], cam['filename'], url, **args)
          p.process()
        except Exception as e:
          print(f"Unable to process webcam {cam['title']}: {e}", file=sys.stderr)
          pass
        finally:
          pass
      ftp.quit()
      ftp = None
      if interval > 0:
        print(f"Sleeping {interval - (time.monotonic() - now)} seconds")
        time.sleep(interval - (time.monotonic() - now))
      else:
        break

  finally:
    if ftp:
      ftp.quit()
