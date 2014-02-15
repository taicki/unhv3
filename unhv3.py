#!/usr/bin/env python
# -*- coding: utf-8 -*-
# HV3 file format: http://www.kippler.com/doc/bond/BondFormat.txt

import struct

def to_int(bytes):
  return struct.unpack("<I", bytes)[0]

def read_chunk_header(fp):
  chunk_name = fp.read(4)
  attr_size = to_int(fp.read(4))
  sub_chunk_size = to_int(fp.read(4))
  chunk_data_size = to_int(fp.read(4))
  return {
    "chunk_name": chunk_name,
    "attr_size": attr_size,
    "sub_chunk_size": sub_chunk_size,
    "chunk_data_size": chunk_data_size,
    "size": 16
  }

def read_attr_chunk(fp):
  name = fp.read(4)
  data_size = to_int(fp.read(4))
  data = fp.read(data_size)
  return {
    "attr_name": name,
    "attr_data_size": data_size,
    "attr_data": data,
    "size": 8 + data_size
  }

def read_chunk(fp):
  header = read_chunk_header(fp)

  attrs = {}
  sub_chunks = []
  chunk_data = None

  if header["attr_size"] > 0:
    nbytes = header["attr_size"]
    while nbytes > 0:
      attr = read_attr_chunk(fp)
      attrs[attr["attr_name"]] = attr
      nbytes -= attr["size"]

  if header["sub_chunk_size"] > 0:
    nbytes = header["sub_chunk_size"]
    while nbytes > 0:
      sub_chunk = read_chunk(fp)
      sub_chunks.append(sub_chunk)
      nbytes -= sub_chunk["size"]

  if header["chunk_data_size"] > 0:
    chunk_data = fp.read(header["chunk_data_size"])

  chunk_size = header["size"] + header["attr_size"] + \
              header["sub_chunk_size"] + header["chunk_data_size"]
  return {
    "header": header,
    "attrs": attrs,
    "sub_chunks": sub_chunks,
    "chunk_data": chunk_data,
    "size": chunk_size
  }


if __name__ == "__main__":
  import os
  import sys

  def usage():
    print "usage: unhv3.py [hv3 file] [dir to unarchive]"
    sys.exit(1)

  if len(sys.argv) != 3:
    usage()

  fp = open(sys.argv[1], "rb")
  hv30 = read_chunk(fp)
  fp.close()

  os.chdir(sys.argv[2])

  head = hv30["sub_chunks"][0]
  file_list = head["sub_chunks"][0]

  body = hv30["sub_chunks"][1]
  files = body["sub_chunks"]

  for i, finf in enumerate(file_list["sub_chunks"]):
    filename = finf["attrs"]["NAME"]["attr_data"].decode("utf-16")[:-1]
    utf8_fn = filename.encode("utf-8")
    print utf8_fn

    f = open(utf8_fn, "wb")
    buf = []
    for pos, val in enumerate(files[i]["chunk_data"]):
      # Decrypt by using XOR based on position. This may not work for some
      # hv3 files
      byte = chr(ord(val) ^ (pos % 256))

      buf.append(byte)
      if len(buf) >= 4096:
        f.write("".join(buf))
        buf = []

    if buf:
      f.write("".join(buf))
    f.close()
