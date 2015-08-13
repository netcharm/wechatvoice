#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import division

import os
import sys

from subprocess import Popen, PIPE, STDOUT
import threading

import wave
import pymedia
import time

# print getattr(sys, 'frozen', False)
# if getattr(sys, 'frozen', False):
#   # frozen
#   CWD = os.path.abspath(os.path.dirname(sys.executable))
# else:
#   CWD = os.path.abspath(os.path.dirname(__file__))

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


########################################################################3
# Simple  audio encoder
def recodeAudio( fName, fOutput, type, bitrate= None ):
  # ------------------------------------

  import pymedia.audio.acodec as acodec
  import pymedia.muxer as muxer
  # Open demuxer

  dm= muxer.Demuxer( fName.split( '.' )[ -1 ].lower() )
  f= open( fName, 'rb' )
  s= f.read( )
  dec= enc= mx= None
  print 'Recoding %s into %s' % ( fName, fOutput )

  frames= dm.parse( s )
  if frames:
    for fr in frames:
      # Assume for now only audio streams

      if dec== None:
        # Open decoder

        dec= acodec.Decoder( dm.streams[ fr[ 0 ] ] )
        print 'Decoder params:\n', dm.streams[ fr[ 0 ] ] , '\n'

      # Decode audio frame

      r= dec.decode( fr[ 1 ] )
      if r:
        if bitrate== None:
          bitrate= r.bitrate

        # Open muxer and encoder

        if enc== None:
          params= { 'id': acodec.getCodecID(type),
                    'bitrate': bitrate,
                    'sample_rate': r.sample_rate,
                    'channels': r.channels }
          print 'Encoder params:\n', params , '\n'
          mx= muxer.Muxer( type )
          stId= mx.addStream( muxer.CODEC_TYPE_AUDIO, params )
          enc= acodec.Encoder( params )
          fw= open(fOutput, 'wb')
          ss= mx.start()
          fw.write(ss)

        enc_frames= enc.encode( r.data )
        if enc_frames:
          for efr in enc_frames:
            ss= mx.write( stId, efr )
            if ss:
              fw.write(ss)

  f.close()

  if fw:
    if mx:
      ss= mx.end()
      if ss:
        fw.write(ss)
    fw.close()

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

def wav2(wav, codec):
  if not os.path.isfile(wav):
    return(None)

  fn = os.path.splitext(wav)
  out = fn[0]+'.'+codec

  recodeAudio(wav, out, codec, 8000)
  return(out)
  pass

def wavconvert(wav, codec):
  from pydub import AudioSegment
  song = AudioSegment.from_wav(wav)

  fn = os.path.splitext(wav)
  out = fn[0]+'.'+codec

  print(time.ctime())
  tags = {'artist': 'Various artists', 'album': 'WeChat Voice', 'year': '', 'comments': 'This album is awesome!'}
  song.export(out, format=codec, parameters=["-q:a", "0"], tags=tags)
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
  target = 'ogg'
  if len(sys.argv) >= 1:
    amr = sys.argv[1]
  if len(sys.argv) >= 2:
    fn = os.path.splitext(sys.argv[2])
    codec = fn[1][1:]

  if amr:
    pcm = amr2pcm(amr)
    wav = pcm2wav(pcm)
    # ogg = wav2(wav, 'ogg')

    ogg = wavconvert(wav, codec)

