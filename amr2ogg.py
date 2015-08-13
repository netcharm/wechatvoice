#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import division

import os
import sys
import glob

from subprocess import Popen, PIPE, STDOUT
import threading

import wave
import time

try:
  CWD = os.path.abspath(os.path.dirname(__file__))
except:
  CWD = os.path.abspath(os.path.dirname(sys.executable))
  # CWD = os.path.abspath(os.path.dirname(sys.argv[0]))

def run(cmd, options=None):
  try:
    if sys.stdout.isatty():
      console = True
  except:
    console = False

  if console:
    p = Popen(cmd, shell=True)
  else:
    # print(cmd)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    # p = Popen(cmd, shell=True, stdout=PIPE)
  if console:
    stdout, stderr = p.communicate()
    return(p.returncode, None, None)
  else:
    if sys.platform in ('win32', 'win64'):
      coding = 'gbk'
    else:
      coding = sys.getdefaultencoding()

    if stdlines:
      st = time.clock()
      lines = []
      while True:
        line = p.stdout.readline()
        if line:
          line = line.strip()
          if len(line) > 0: lines.append(line)
        else:
          break
        if (time.clock() - st >= 0.2) and (len(lines) > 0):
          stdlines.append('\n'.join(lines).decode(coding))
          stdlines.moveCursor(11)
          lines[:] = []
          st = time.clock()

      try:
        stdlines.append('\n'.join(lines).decode(coding))
        stdlines.moveCursor(11)
      except:
        pass

      # stdout, stderr = p.communicate()
      # return(p.returncode, stdout.decode(coding))
      p.wait()
      return(p.returncode, None, None)
    else:
      stdout, stderr = p.communicate()
      print(stdout.decode(coding))
      print(stderr.decode(coding))
      return(p.returncode, stdout.decode(coding), stderr.decode(coding))

  # print 'return code : %s' % p.returncode # is 0 if success
  pass

def amr2pcm(amr):
  if not os.path.isfile(amr):
    return(None)

  with open(amr, 'r+b') as amrfile:
    amrdata = amrfile.read()
    if amrdata[:len('#!SILK_V3')] != '#!SILK_V3':
      amrfile.seek(0)
      amrfile.write(amrdata[1:])
      amrfile.truncate(len(amrdata)-1)

  cmd = os.path.join(CWD, 'decoder.exe')

  options = []
  options.append('-Fs_API 8000')

  fn = os.path.splitext(amr)
  fin = amr
  fout = fn[0]+'.pcm'

  cmdline = '"%s" "%s" "%s" %s' % (cmd, fin, fout, ' '.join(options))

  # print(cmdline)
  ret = run(cmdline)

  return(fout)
  pass

def pcm2wav(pcm):
  if not os.path.isfile(pcm):
    return(None)
  with open(pcm, 'rb') as pcmfile:
    pcmdata = pcmfile.read()
    # wavfile.setparams((2, 2, 44100, 0, 'NONE', 'NONE'))
    # wavfile.setparams((2, 1, 8000, 242, 'NONE', 'NONE'))

    #Wave_write.setnchannels(n)
    #Set the number of channels.
    #
    #Wave_write.setsampwidth(n)
    #Set the sample width to n bytes.
    #
    #Wave_write.setframerate(n)
    #Set the frame rate to n.
    #
    #Wave_write.setnframes(n)
    #Set the number of frames to n. This will be changed later if more frames are written.
    #
    #Wave_write.setcomptype(type, name)
    #Set the compression type and description. At the moment, only compression type NONE is supported, meaning no compression.
    #
    #Wave_write.setparams(tuple)
    #The tuple should be (nchannels, sampwidth, framerate, nframes, comptype, compname), with values valid for the set*() methods. Sets all parameters.
    #
    fn = os.path.splitext(pcm)
    wav = fn[0]+'.wav'
    wavfile = wave.open(wav, 'wb')

    wavfile.setnchannels(1)
    wavfile.setsampwidth(2)
    wavfile.setframerate(8000)
    wavfile.setnframes(0)

    wavfile.writeframes(pcmdata)

    wavfile.close()

    return(wav)
  pass

def wavconvert(wav, codec):
  from pydub import AudioSegment
  song = AudioSegment.from_wav(wav)

  fn = os.path.splitext(wav)
  out = fn[0]+'.'+codec

  tags = {
          'artist'  : 'Various artists',
          'album'   : 'WeChat Voice',
          'year'    : time.strftime('%Y-%m-%d'),
          'comments': 'This album is awesome!'
         }

  q = '0'
  if codec.lower() == 'ogg':
    q = '0'
  elif codec.lower() in ['mp3', 'mp2', 'mpa']:
    q = '6'
  elif codec.lower() in ['aac', 'm4a']:
    codec = 'mp4'

  song.export(out, format=codec, parameters=["-q:a", q], tags=tags)
  return(out)
  pass

def clean(pcm, wav):
  if os.path.isfile(pcm):
    os.remove(pcm)
  if os.path.isfile(wav):
    os.remove(wav)
  pass


if __name__ == '__main__':
  amr = None
  out = None
  codec = 'ogg'
  if len(sys.argv) > 1:
    fin = sys.argv[1]
  if len(sys.argv) > 2:
    fn = os.path.splitext(sys.argv[2])
    codec = fn[1][1:]

  if fin:
    files = glob.glob(fin)
    for amr in files:
      pcm = amr2pcm(amr)
      wav = pcm2wav(pcm)
      out = wavconvert(wav, codec)
      clean(pcm, wav)
      print('%s has converted to %s.\n' % (amr, out))

