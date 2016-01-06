#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import sys
import codecs

import sqlite3
# from pysqlcipher import dbapi2 as sqlite3


def getFileIndex(db, filename):
    fileindex = -1

    # Create query
    query = 'SELECT * FROM apk_file_info WHERE file_path LIKE "%%%s";' % (filename)
    
    # Open database, set up cursor to read database   
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Execute query
    cur.execute(query)

    try:
        fileindex = 0
        for index, row in enumerate(cur):
            # print(row[3], row[4])
            fileindex = row[4]
            break
    except:
        pass
        
    cur.close()
    
    return(fileindex)    

def getFileData(db, fileindex, filename):
    status = False
        
    if filename == None: return(status)
    
    # Create query
    query = 'SELECT * FROM apk_file_data WHERE file_index=%d;' % (fileindex)

    # Open database, set up cursor to read database
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Execute query
    cur.execute(query)

    # Go through returned rows
    try:
        with codecs.open(u'%s' % filename, 'wb') as f:
            for index, row in enumerate(cur):
                # Get the first (zero’th) column from the returned row
                dataIndex  = row[0]
                fileIndex  = row[1]
                fileLength = row[2]
                fileData   = row[3]
                
                f.write(fileData)

            # close the file
            f.close()
            status = True
    except:
        pass

    cur.close()

    return(status)

def extract(db, file, force=False):
    status = False
    if not os.path.isfile(file) or force:
        index = getFileIndex(db, file)
        if index >= 0:
            status = getFileData(db, index, file)
            if status:
                print(u'%s extracted from huawei backup database blob.' % file)
            else:
                print(u'%s extracting from huawei backup database blob failed!' % file)

    return(status)
    
if __name__ == '__main__':
    pass