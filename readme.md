intro
=====
these utils is used for converting wechat voice(aud/amr) to ogg/mp3/mp4/m4a/aac

features
========
1. fixing the aud/amr magic header for decode it
2. converting fixed aud/amr file to audio file you like, etc.: ogg/mp3/aac

requirement
===========
1. python 2.7.x
2. Skype Silk SDK
3. latest FFMpeg binary
4. pydub

usage
=====
1. If you like, you can download latest Skype Silk SDK to build decoder.exe,
   otherwise you can using the decoder.exe compiled by me
2. download latest FFMpeg binary from https://www.ffmpeg.org
3. download pydub and install it to python, or using pydub dist package in this repo.
4. mk.cmd using cxFreeze to making a console exe
5. usage:
   `amr2ogg.py <*.amr|input.amr> [ogg|mp3|mp4|m4a]`

bugs
====


license
=======
1. decoder.exe is follow original by Skype/Microsoft
2. pydub is follow original.
3. My owner code is follow MIT License.

source
=======
1. https://github.com/netcharm/wechatvoiceconvert
2. https://bitbucket.org/netcharm/wechatvoice
