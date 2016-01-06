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
from pysqlcipher import dbapi2 as sqlite3

from dataio import huawei


MAX_LINE_CHAR = 80        

if sys.platform in ('win32', 'win64'):
    encoding = 'gbk'
else:
    encoding = sys.getdefaultencoding()


def field(field):
    return(unicode(field).encode('utf8'))        
    
def getUIN(db, file):
    uin = ''
    if os.path.isfile(file):
        try:    
            doc = etree.parse(file)
            nodes = doc.xpath('//int[@name="default_uin"]')
            for node in nodes:
                uin = node.attrib['value']
                break
        except:
            pass

    return(uin)
    
def calcKey(imei, uin):
    password = '%s%s' % (imei, uin)
    md5 = hashlib.md5(password)
    password = md5.hexdigest()[:7]

    return(password)
    
def setDecryptParams(cur, key):
    status = False
    if cur!=None and key != None:
        if isinstance(cur, sqlite3.Cursor):
            cur.execute( 'PRAGMA key = "%s";' % key )
            cur.execute( 'PRAGMA cipher_use_hmac = OFF;' )
            cur.execute( 'PRAGMA cipher_page_size = 1024;' )
            cur.execute( 'PRAGMA kdf_iter = 4000;' )
            cur.execute( "PRAGMA cipher_migrate" )
            status = True
    else:
        print(u'KEY not given for Encrypted DB file!')
    
    return(status)

def getDecryptFile(db, key, fileIn, fileOut ):
    status = False

    if not os.path.isfile(fileOut):
        # 
        # code source: http://articles.forensicfocus.com/2014/10/01/decrypt-wechat-enmicromsgdb-database/
        # 
        conn = sqlite3.connect( u'%s' % fileIn )
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if setDecryptParams(cur, key):		
            try:
                print( u'Decrypting...' )
                cur.execute( 'ATTACH DATABASE "%s" AS wechatdecrypted KEY "";' % fileOut)
                cur.execute( 'SELECT sqlcipher_export( "wechatdecrypted" );' )
                cur.execute( 'DETACH DATABASE wechatdecrypted;' )
                print( u'Detaching database...' )
                cur.close()
                status = True
            except:
                print(u'Decrypting failed!')
                pass
                
        cur.close()
	
    return(status)

def getSex(sex):
    if sex == '1':
        return('Male')
    elif sex == '2':
        return('Female')
    else:
        return('Unknown')

def getMsgType(typeNo):
    msgType = None
    if typeNo == 0x13000031:
        msgType = 'ServicePush'
    elif typeNo == 0x11000031:
        msgType = 'SubscribePush'
    elif typeNo == 0x00000031:
        msgType = 'SubscribePush'

    return(msgType)

def getFriendList(db, decrypted=True, key=None):
    friends = dict()

    # Create query
    # query = 'SELECT * FROM ContactLabel WHERE file_path LIKE "%%%s";' % (filename)
    query = 'SELECT DISTINCT r.username,r.alias,r.nickname,r.encryptUsername,r.conRemark,r.contactLabelIds,f.sex,f.province,f.city,f.signature,g.imgflag,g.reserved1,g.reserved2 FROM rcontact r LEFT OUTER JOIN friend_ext f ON f.username=r.username OR f.username=r.encryptUsername LEFT OUTER JOIN img_flag g ON g.username=r.username WHERE (r.verifyFlag=0 or r.verifyFlag=56) AND r.type!=33;'
    
    # Open database, set up cursor to read database   
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if not decrypted:
        if not setDecryptParams(cur, key):
            cur.close()
            return(contacts)
    
    # Execute query
    cur.execute(query)
    try:
        for index, row in enumerate(cur):
            # print(u'%s: %s' % (row[0], row[4]))
            user_id      = row[0]
            user_alias   = row[1] if row[1] else ''
            user_nick    = row[2] if row[2] else ''
            user_encrypt = row[3] 
            user_remark  = row[4] if row[4] else ''
            user_labels  = row[5]
            user_sex     = getSex(row[6]) 
            user_loc     = u'%s, %s' % (row[8], row[7])
            user_sig     = row[9] if row[9] else ''
            user_img     = {'flag':row[10], '0':[11], '96':[12]}
            # contacts.append({'id':user_id, 'alias':user_alias, 'nick':user_nick, 'encrypt':user_encrypt, 'remark':user_remark, 'labels':user_labels, 'sex':user_sex, 'location':user_loc, 'signature':user_sig, 'image':user_img})
            friends[user_id] = {'id':user_id, 'alias':user_alias, 'nick':user_nick, 'encrypt':user_encrypt, 'remark':user_remark, 'labels':user_labels, 'sex':user_sex, 'location':user_loc, 'signature':user_sig, 'image':user_img}
    except:
        pass

    cur.close()
    
    return(friends)

def getContactList(db, decrypted=True, key=None):
    contacts = dict()

    # Create query
    # query = 'SELECT * FROM ContactLabel WHERE file_path LIKE "%%%s";' % (filename)
    query = 'SELECT DISTINCT r.username,r.alias,r.nickname,r.encryptUsername,r.conRemark,r.contactLabelIds,f.sex,f.province,f.city,f.signature,g.imgflag,g.reserved1,g.reserved2 FROM rcontact r LEFT OUTER JOIN friend_ext f ON f.username=r.username OR f.username=r.encryptUsername LEFT OUTER JOIN img_flag g ON g.username=r.username;'
    
    # Open database, set up cursor to read database   
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if not decrypted:
        if not setDecryptParams(cur, key):
            cur.close()
            return(contacts)
    
    # Execute query
    cur.execute(query)
    try:
        for index, row in enumerate(cur):
            # print(u'%s: %s' % (row[0], row[4]))
            user_id      = row[0]
            user_alias   = row[1] if row[1] else ''
            user_nick    = row[2] if row[2] else ''
            user_encrypt = row[3]
            user_remark  = row[4] if row[4] else ''
            user_labels  = row[5]
            user_sex     = getSex(row[6]) 
            user_loc     = u'%s, %s' % (row[8], row[7])
            user_sig     = row[9] if row[9] else ''
            user_img     = {'flag':row[10], '0':[11], '96':[12]}
            # contacts.append({'id':user_id, 'alias':user_alias, 'nick':user_nick, 'encrypt':user_encrypt, 'remark':user_remark, 'labels':user_labels, 'sex':user_sex, 'location':user_loc, 'signature':user_sig, 'image':user_img})
            contacts[user_id] = {'id':user_id, 'alias':user_alias, 'nick':user_nick, 'encrypt':user_encrypt, 'remark':user_remark, 'labels':user_labels, 'sex':user_sex, 'location':user_loc, 'signature':user_sig, 'image':user_img}
    except:
        pass

    cur.close()
    
    return(contacts)

def getSubscribeList(db, decrypted=True, key=None):
    subscribes = dict()

    # Create query
    # query = 'SELECT * FROM ContactLabel WHERE file_path LIKE "%%%s";' % (filename)
    query = 'SELECT DISTINCT r.username,r.alias,r.nickname,r.encryptUsername,r.conRemark,r.contactLabelIds,g.imgflag,g.reserved1,g.reserved2 FROM rcontact r LEFT OUTER JOIN img_flag g ON g.username=r.username WHERE r.verifyFlag=24 AND r.encryptUsername NOT NULL AND r.encryptUsername !="";'
    
    # Open database, set up cursor to read database   
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if not decrypted:
        if not setDecryptParams(cur, key):
            cur.close()
            return(contacts)
    
    # Execute query
    cur.execute(query)
    try:
        for index, row in enumerate(cur):
            # print(u'%s: %s' % (row[0], row[4]))
            user_id = row[field('username')]
            user_alias = row[field('alias')]
            user_nick = row[field('nickname')]
            user_encrypt = row[field('encryptUsername')]
            user_remark = row[field('conRemark')]
            user_labels = row[field('contactLabelIds')]
            user_img = {'flag':row[field('imgflag')], '0':[field('reserved1')], '96':[field('reserved2')]}
            subscribes[user_id] = {'id':user_id, 'alias':user_alias, 'nick':user_nick, 'encrypt':user_encrypt, 'remark':user_remark, 'labels':user_labels, 'image':user_img}
    except:
        pass

    cur.close()
    
    return(subscribes)

def getChatroomList(db, decrypted=True, key=None):
    chatrooms = dict()

    contacts = getContactList(db, decrypted=decrypted, key=key)
    
    # Create query
    query = 'SELECT r.chatroomname,r.chatroomnick,r.roomowner,r.memberlist,r.displayname FROM chatroom r;'
    
    # Open database, set up cursor to read database   
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if not decrypted:
        if not setDecryptParams(cur, key):
            cur.close()
            return(chatrooms)
    
    # Execute query
    cur.execute(query)
    try:
        for index, row in enumerate(cur):            
            chat_name  = 'Unknown' if row[0] == None else row[0]
            # chat_nick  = chat_name if row[1] == None else row[1]
            chat_nick  = contacts[row[0]]['nick']
            chat_owner = 'Unknown' if row[2] == None else row[2]
            # chat_members = zip(row[3].split(u';'), row[4].split(u'、'))
            chat_members = map(lambda x: {'name':x[0], 'nick':x[1]}, zip(row[3].split(u';'), row[4].split(u'、')))
            # chat_displays = map(lambda x: u'%s[%s]' % (x[1], x[0]), chat_members)
            # chatrooms.append({'name':chat_name, 'nick':chat_nick, 'owner':chat_owner, 'members':chat_members})
            chatrooms[chat_name] = {'name':chat_name, 'nick':chat_nick, 'owner':chat_owner, 'members':chat_members}
    except:
        pass

    cur.close()

    return(chatrooms)

def getMessages(db, user, decrypted=True, key=None, limit=-1, offset=0):
    chatlist = []

    # Create query
    # query = 'SELECT datetime(subStr(cast(m.createTime as text),1,10),"unixepoch","localtime") AS time,case m.isSend WHEN 0 THEN r.nickname WHEN 1 THEN "我" END AS talker,m.talker AS userid,m.content,m.type,m.status,m.imgPath FROM message m INNER JOIN rcontact r ON m.talker = r.username WHERE m.type=1 AND r.nickname = "%s" ORDER BY time LIMIT %d OFFSET %d;' % (user, limit, offset)
    query = 'SELECT datetime(subStr(cast(m.createTime as text),1,10),"unixepoch","localtime") AS time,case m.isSend WHEN 0 THEN r.nickname WHEN 1 THEN "我" END AS talker,m.talker AS userid,m.content,m.type,m.status,m.imgPath FROM message m INNER JOIN rcontact r ON m.talker = r.username WHERE r.nickname = "%s" ORDER BY time LIMIT %d OFFSET %d;' % (user, limit, offset)    
    # Open database, set up cursor to read database   
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if not decrypted:
        if not setDecryptParams(cur, key):
            cur.close()
            return(result)
        
    # Execute query
    cur.execute(query)
    try:
        for index, row in enumerate(cur):
            msg_time    = row[field(u'time')]    # row[0]
            msg_talker  = row[field(u'talker')]  # row[1]
            msg_userid  = row[field(u'userid')]  # row[2]
            msg_content = row[field(u'content')] # row[3]
            msg_type    = row[field(u'type')]    # row[4]
            msg_status  = row[field(u'status')]  # row[5]
            msg_image   = row[field(u'imgPath')] # row[6]
            # msg_
            chatlist.append({'time':msg_time, 'talker':msg_talker, 'userid':msg_userid, 'content':msg_content,'type':msg_type, 'status':msg_status, 'image':msg_image})
            pass
        pass
    except:
        pass

    cur.close()

    return(chatlist)


def getFuncTemplate(db, decrypted=True, key=None):
    results = []

    # Create query
    query = 'SELECT * FROM friend_ext;'
    
    # Open database, set up cursor to read database   
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if not decrypted:
        if not setDecryptParams(cur, key):
            cur.close()
            return(result)
        
    # Execute query
    cur.execute(query)
    try:
        for index, row in enumerate(cur):
            pass
    except:
        pass

    cur.close()

    return(results)


def main(db, imei, user=None):
    print(u'='*MAX_LINE_CHAR)

    file_pref = 'system_config_prefs.xml' 
    uin = getUIN(db, file_pref)
    print(u'UIN: %s' % uin)
    print(u'-'*MAX_LINE_CHAR)
    
    key = calcKey(imei, uin)
    print(u'KEY: %s' % key)
    print(u'-'*MAX_LINE_CHAR)
        
    file_db = 'EnMicroMsg.db'      
    file_db_decrypted = 'EnMicroMsg_Decrypted.db'
    getDecryptFile(db, key, file_db, file_db_decrypted)
    print(u'%s decrypted from encrypted %s database.' % ( file_db_decrypted, file_db ))
    print(u'-'*MAX_LINE_CHAR)
    
    # contacts = getContactList(file_db_decrypted, decrypted=True, key=None)
    friends = getFriendList(file_db, decrypted=False, key=key)
    # print(contacts)
    id = 0
    for k in friends:
        id += 1
        friend = friends[k]
        print(u'%04d: [%s] -> [%s][%s][%s][%s][%s][%s][%s]' % (id, friend['id'], friend['nick'], friend['alias'], friend['remark'], friend['encrypt'], friend['labels'], friend['location'], friend['signature']))        
    print(u'Got all friend list.')
    print(u'-'*MAX_LINE_CHAR)

    contacts = getContactList(file_db, decrypted=False, key=key)
    print(u'Got all contacts list.')
    print(u'-'*MAX_LINE_CHAR)

    # contacts = getContactList(file_db_decrypted, decrypted=True, key=None)
    subscribes = getSubscribeList(file_db, decrypted=False, key=key)
    # print(contacts)
    id = 0
    for k in subscribes:
        id += 1
        subscribe = subscribes[k]
        print(u'%04d: [%s] -> [%s][%s][%s][%s]' % (id, subscribe['id'], subscribe['nick'], subscribe['alias'], subscribe['remark'], subscribe['encrypt']))        
    print(u'Got all subscribe list.')
    print(u'-'*MAX_LINE_CHAR)
        
    chatrooms = getChatroomList(file_db, decrypted=False, key=key)
    id_chat = 0
    for k in chatrooms:
        id_chat += 1
        chatroom = chatrooms[k]
        members = chatroom['members']
        # print(u'%04d: %s [%s]' % (id_chat, contacts[chatroom['name']]['nick'], chatroom['name']))
        print(u'%04d: %s [%s]' % (id_chat, chatroom['nick'], chatroom['name']))
        id_member = 0
        for member in members:
            id_member += 1
            # print(u'\t%04d: %s [%s] ' % (id_member, member[1], member[0]))
            print(u'\t%04d: %s [%s] ' % (id_member, member['nick'], member['name']))
        print(u'')
    print(u'-'*MAX_LINE_CHAR)
    
    if user: 
        chats = getMessages(file_db, user, decrypted=False, key=key)
        id = 0
        for chat in chats:
            id += 1
            talker = chat['talker']                                         
            content = None if chat['content'] == None else '\n'.join(chat['content'].split())
            try:
                if chat['talker'] != '我':
                    talker = contacts[chat['userid']]['remark'] if contacts[chat['userid']]['remark'] else contacts[chat['userid']]['nick'] 
                    if chat['userid'].endswith('@chatroom'):
                        idx = chat['content'].find(':')
                        if idx >= 0:                       
                            talker = chat['content'][:idx]
                    talker_nick = contacts[talker]['nick']
                    talker_alias = contacts[talker]['alias'] 
                    talker_remark = contacts[talker]['remark']
                    if talker_remark : talker = talker_remark
                    elif talker_alias : talker = talker_alias
                    else: talker = talker_nick  
                    talker = u'%s' % (talker)
                    content = '\n'.join(chat['content'].split()[1:])
                else:
                    talker = chat['talker']                                         
            except:
                pass
            line = u'%04d: [%s]@[%s] : [%s]' % (id, chat['time'], talker, content) 
            print(line.encode(encoding, 'ignore'))        
        print(u'-'*MAX_LINE_CHAR)
        
    print(u'='*MAX_LINE_CHAR)
    return

    
if __name__ == '__main__':
    # Get database/IMEI from command line
    db = sys.argv[1]
    imei = sys.argv[2]
    
    user = None if len(sys.argv) < 4 else sys.argv[3].decode(encoding)

    if not huawei.extract(db, 'facebook.db', force=True): print('facebook.db not exists!')
    if not huawei.extract(db, 'enFavorite.db', force=True): print('enFavorite.db not exists!')
    
    # main(db, imei, user)
    