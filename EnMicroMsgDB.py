#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import sys
import codecs
import hashlib
import re
from lxml import etree


# import sqlite3
# from pysqlcipher import dbapi2 as sqlite3cipher
from pysqlcipher import dbapi2 as sqlite3

def getUIN(file):
    uin = None
    doc = etree.parse(file)
    nodes = doc.xpath('//int[@name="default_uin"]')
    for node in nodes:
        uin = node.attrib['value']
        break

    return(uin)
    
def calcPassword(imei, uin):
    password = '%s%s' % (imei, uin)
    md5 = hashlib.md5(password)
    password = md5.hexdigest()[:7]

    return(password)
    

def getFileIndex(db, filename):
    # select * from apk_file_info where file_path like "%EnMicroMsg%";
    # file_index = 605

    # Create query
    query = 'SELECT * FROM apk_file_info WHERE file_path LIKE "%%%s";' % (filename)
    
    # Open database, set up cursor to read database   
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    # Execute query
    cur.execute(query)

    try:
        fileindex = 0
        for index, row in enumerate(cur):
            # print(row[3], row[4])
            fileindex = row[4]
            break
        
        cur.close()
    except:
        cur.close()
        fileindex = -1
    
    return(fileindex)    

def getFileData(db, fileindex, filename):
    if filename == None: return
    
    # Pick tables/fields to work with
    # select * from apk_file_data where file_index=605;
    

    # Create query
    query = u'SELECT * FROM apk_file_data WHERE file_index=%d;' % (fileindex)

    # Open database, set up cursor to read database
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # Execute query
    cur.execute(query)

    # Go through returned rows
    try:
        with codecs.open(u'%s' % filename, 'wb') as f:
            for index, row in enumerate(cur):
                # Get the first (zero’th) column from the returned row
                dataIndex = row[0]
                fileIndex = row[1]
                fileLength = row[2]
                fileData = row[3]
                
                print(dataIndex, fileLength)
                # Check if the data is binary, open the file in binary or text mode
                # accordingly and write the data out.
                f.write(fileData)

            # close the file
            f.close()
        cur.close()
        status = 0
    except:
        cur.close()
        status = 1    

    return(status)

def setDecryptParams(cur, key):
    if isinstance(cur, sqlite3.Cursor):
        cur.execute( 'PRAGMA key = "' + key + '";' )
        cur.execute( 'PRAGMA cipher_use_hmac = OFF;' )
        cur.execute( 'PRAGMA cipher_page_size = 1024;' )
        cur.execute( 'PRAGMA kdf_iter = 4000;' )
    return()

def getDecryptFile( key, fileIn, fileOut ):
    # 
    # code source: http://articles.forensicfocus.com/2014/10/01/decrypt-wechat-enmicromsgdb-database/
    # 
	# conn = sqlite3cipher.connect( u'%s' % fileIn )
    conn = sqlite3.connect( u'%s' % fileIn )
    cur = conn.cursor()
    setDecryptParams(cur, key)		
    # cur.execute( 'PRAGMA key = "' + key + '";' )
    # cur.execute( 'PRAGMA cipher_use_hmac = OFF;' )
    # cur.execute( 'PRAGMA cipher_page_size = 1024;' )
    # cur.execute( 'PRAGMA kdf_iter = 4000;' )
    try:
        print( 'Decrypting...' )
        cur.execute( 'ATTACH DATABASE "%s" AS wechatdecrypted KEY "";' % fileOut)
        cur.execute( 'SELECT sqlcipher_export( "wechatdecrypted" );' )
        cur.execute( 'DETACH DATABASE wechatdecrypted;' )
        print( 'Detaching database...' )
        cur.close()
        status = 0
    except:
        cur.close()
        status = 1
	
    return(status)

def getContactList(db, decrypted=True, key=None):
    def getSex(sex):
        if sex == '1':
            return('Male')
        elif sex == '2':
            return('Female')
        else:
            return('Unknown')


    contacts = []

    # Create query
    # query = 'SELECT * FROM ContactLabel WHERE file_path LIKE "%%%s";' % (filename)
    query = 'SELECT f.username,f.sex,f.province,f.city,f.signature,g.imgflag,g.reserved1,g.reserved2 FROM friend_ext f join img_flag g on f.username = g.username;'
    
    # Open database, set up cursor to read database   
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    if not decrypted:
        if key != None:
            cur.execute( 'PRAGMA key = "' + key + '";' )
            cur.execute( 'PRAGMA cipher_use_hmac = OFF;' )
            cur.execute( 'PRAGMA cipher_page_size = 1024;' )
            cur.execute( 'PRAGMA kdf_iter = 4000;' )
        else:
            print(u'KEY not given for Encrypted DB file!')
            cur.close()
            return(contacts)
    
    # Execute query
    cur.execute(query)
    try:
        for index, row in enumerate(cur):
            # print(u'%s: %s' % (row[0], row[4]))
            user_id = row[0]
            user_sex = getSex(row[1]) # row[1] == '1' ? 'male' : 'female' 
            user_loc = u'%s, %s' % (row[3], row[2])
            user_sig = row[4]
            user_img = {'flag':row[5], '0':[6], '96':[7]}
            contacts.append({'id':user_id, 'sex':user_sex, 'location':user_loc, 'signature':user_sig, 'image':user_img})
        
        cur.close()
    except:
        cur.close()
        fileindex = -1
    
    print(contacts)
    return(contacts)


        
if __name__ == '__main__':
    # Get database/IMEI from command line
    db = sys.argv[1]
    imei = sys.argv[2]

    print(u'='*80)

    file_pref = 'system_config_prefs.xml' 
    if not os.path.isfile(file_pref):
        index = getFileIndex(db, file_pref)
        getFileData(db, index, file_pref)
    uin = getUIN(file_pref)
    print(u'UIN: %s' % uin)
    print(u'-'*80)
    
    key = calcPassword(imei, uin)
    print(u'KEY: %s' % key)
    print(u'-'*80)
        
    file_db = 'EnMicroMsg.db'
    if not os.path.isfile(file_db):
        index = getFileIndex(db, file_db)
        getFileData(db, index, file_db)
        
    file_db_decrypted = 'EnMicroMsg_Decrypted.db'
    if not os.path.isfile(file_db_decrypted):
        getDecryptFile(key, file_db, file_db_decrypted)
    
    # getContactList(file_db_decrypted)
    getContactList(file_db, decrypted=False, key=key)
    
    print(u'='*80)
    