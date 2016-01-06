#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import sys

import threading

import codecs

from lxml import etree

try:
    import simplejson as json
except:
    import json

import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import Qt, QMetaObject, QString, QSize, QThread, pyqtSlot, Q_ARG, QLocale
from PyQt4.QtGui import QIcon, QDialog, QFileDialog, QColor, QFont, QTreeWidgetItem, QListWidgetItem

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

from EnMicroMsgDB import *

SCRIPTNAME = ''
try:
    SCRIPTNAME = __file__
except:
    SCRIPTNAME = sys.argv[0]

CWD = os.path.abspath(os.path.dirname(SCRIPTNAME))


class WeChatMsgWindow(QtGui.QMainWindow):
    ui_main = None
    UIFILE_MAIN = 'MicroMsg.ui'
    ICONFILE = 'WeChat-Icon.png'
    
    TITLE = None

    db = 'com.tencent.mm.db'
    uin = None
    imei = None
    key = None
    decrypted = False
    
    file_pref = 'system_config_prefs.xml' 
    file_db = 'EnMicroMsg.db'
    file_db_decrypted = 'EnMicroMsg_Decrypted.db'

    friends = dict()
    contacts = dict()
    chatrooms = dict()
    subscribes = dict()
    
    contacts_alias = dict()
    contacts_nick = dict()
    contacts_remark = dict()
    
    chatlist = []
    
    def __init__(self, imei=None, decrypted=False):
        QtGui.QMainWindow.__init__(self)

        ui_file = os.path.join(CWD, self.UIFILE_MAIN)
        if os.path.isfile(ui_file):
            self.ui_main = uic.loadUi(ui_file)
            # self.ui_main.windowIcon(self.ICON)
            self.ui_main.show()
            self.TITLE = self.ui_main.windowTitle()
           
            app.setWindowIcon(QtGui.QIcon('chip_icon_normal.png'))
            print(self.TITLE)
            
            #
            # connect treeview item change event
            #
            QtCore.QObject.connect(self.ui_main.tvUser, QtCore.SIGNAL('currentItemChanged(QTreeWidgetItem *, QTreeWidgetItem *)'), self.userSelected)
            
            #
            # connect extract menu item
            #
            QtCore.QObject.connect(self.ui_main.actionFromHuaweiBackup, QtCore.SIGNAL('activated()'), self.extractFromHuaweiBackup)
            QtCore.QObject.connect(self.ui_main.actionDecryptDB, QtCore.SIGNAL('activated()'), self.decryptDB)


            self.imei = imei
            self.decrypted = decrypted
            self.uin = getUIN(self.db, self.file_pref)
            self.key = calcKey(self.imei, self.uin)
            print(self.uin, self.key)
            # self.ui_main
            
            self.friends = getFriendList(self.file_db, decrypted=self.decrypted, key=self.key)
            self.contacts = getContactList(self.file_db, decrypted=self.decrypted, key=self.key)
            self.chatrooms = getChatroomList(self.file_db, decrypted=self.decrypted, key=self.key)
            self.subscribes = getSubscribeList(self.file_db, decrypted=self.decrypted, key=self.key)

            for k in self.contacts:
                user = self.contacts[k]
                if user['remark']:
                    self.contacts_remark[user['remark']] = user
                if user['nick']:
                    self.contacts_remark[user['nick']] = user
                if user['alias']:
                    self.contacts_alias[user['alias']] = user
                    
            
            self.showContacts()
        pass

    @pyqtSlot(QTreeWidgetItem, QTreeWidgetItem)
    def userSelected(self, newUser, oldUser):
        # userItem = self.ui_main.tvUser.currentItem()
        if newUser:
            user = newUser.data(0, Qt.UserRole)
            if user:
                # print(unicode(user[QString('nick')]).encode('gbk'))
                self.showMessage(unicode(user[QString('nick')]))
        
        pass

    @pyqtSlot()
    def extractFromHuaweiBackup(self):
        status = extractFromHuaweiBackupDB(self.db, self.file_pref)
        status = extractFromHuaweiBackupDB(self.db, self.file_db)
        pass

    @pyqtSlot()
    def decryptDB(self):
        status = getDecryptFile(self.key, self.file_db, self.file_db_decrypted)
        status = extractFromHuaweiBackupDB(self.db, self.file_pref)
        status = extractFromHuaweiBackupDB(self.db, self.file_db)
        pass

    def findUser(self, user):
        if user in self.contacts:
            return (self.contacts[user])
        if user in self.contacts_remark:
            return (self.contacts_remark[user])
        if user in self.contacts_nick:
            return (self.contacts_nick[user])
        if user in self.contacts_alias:
            return (self.contacts_alias[user])
        return(None)
                
    def showContacts(self):
        font = QFont()
        font.setWeight(QFont.Bold)

        self.ui_main.tvUser.setHeaderLabel('Contacts')
        
        #
        # display chatroom list
        #
        item_chatrooms = QTreeWidgetItem(self.ui_main.tvUser)
        item_chatrooms.setFont(0, font)
        item_chatrooms.setText(0, "Chatrooms")
        item_chatrooms.setExpanded(True)

        chatroom_nicks = dict()
        id_chat = 0
        for k in self.chatrooms:
            id_chat += 1
            chatroom = self.chatrooms[k]
            members = chatroom['members']
            item_chatroom = QTreeWidgetItem(item_chatrooms)
            item_chatroom.setText(0, self.friends[chatroom['name']]['nick'])
            item_chatroom.setData(0, Qt.UserRole, chatroom)
            item_chatroom.setToolTip(0, chatroom['name'])
            chatroom_nicks[unicode(item_chatroom.text(0))] = True 
            
            #
            # display chatroom member list
            #
            id_member = 0
            for member in members:
                id_member += 1
                user = self.findUser(member['name'])                
                user_nick   = user['nick'] if user else member['nick'] 
                user_alias  = user['alias'] if user else ''
                user_remark = user['remark'] if user else ''
                user_sign   = user['signature'] if user else ''
                item_member = QTreeWidgetItem(item_chatroom)
                item_member.setText(0, member['nick'] if member['nick'] else member['name'])
                item_member.setData(0, Qt.UserRole, member)
                item_member.setToolTip(0, '%s [%s]\n%s' % (member['nick'], member['name'], user_sign))

        #
        # display friend list
        #
        item_friends = QTreeWidgetItem(self.ui_main.tvUser)
        item_friends.setFont(0, font)
        item_friends.setText(0, "Friends")
        item_friends.setExpanded(True)

        id = 0
        for k in self.friends:
            id += 1
            friend = self.friends[k]
            if friend['nick'] in chatroom_nicks: continue

            user = self.findUser(friend['nick'])                
            user_nick   = user['nick'] if user else member['nick'] 
            user_alias  = user['alias'] if user else ''
            user_remark = user['remark'] if user else user_nick
            user_sign   = user['signature'] if user else ''
            
            item_friend = QTreeWidgetItem(item_friends)
            item_friend.setText(0, friend['remark'] if friend['remark'] else friend['nick'])
            item_friend.setData(0, Qt.UserRole, friend)
            item_friend.setToolTip(0, '%s [%s]\n%s' % (friend['nick'], friend['id'], user_sign))

        #
        # display subscribe list
        #
        item_subscribes = QTreeWidgetItem(self.ui_main.tvUser)
        item_subscribes.setFont(0, font)
        item_subscribes.setText(0, "Subscribes")
        item_subscribes.setExpanded(True)

        id = 0
        for k in self.subscribes:
            id += 1
            subscribe = self.subscribes[k]
            item_subscribe = QTreeWidgetItem(item_subscribes)
            item_subscribe.setText(0, subscribe['remark'] if subscribe['remark'] else subscribe['nick'])
            item_subscribe.setData(0, Qt.UserRole, subscribe)
            item_subscribe.setToolTip(0, subscribe['nick'])

        pass

    def replaceUserId(self, content):
        text = content
        if text:
            for k in self.contacts:
                user_id     = self.contacts[k]['id']
                user_nick   = self.contacts[k]['nick']
                user_alias  = self.contacts[k]['alias'] 
                user_remark = self.contacts[k]['remark']
                if user_remark :  user = user_remark
                elif user_alias : user = user_alias
                else:             user = user_nick
                
                if user_id and user:
                    text = text.replace('@%s' % user_id, '@%s' % user)
                    text = text.replace('%s:' % user_id, '%s:' % user)
    
        text = text.replace('><', '>\n<')
        return(text)

    def formatMessage(self, msg_content):
        msg = dict()
        
        doc = etree.fromstring(msg_content)
        msg['type'] = 'text'
        msg['data'] = None
        msg['content'] = etree.tostring(doc, pretty_print=True, encoding='unicode') #, xml_declaration=False)

        emoji = dict()
        appmsg = dict()
        image = dict()
        
        emoji_nodes = doc.xpath('//emoji')
        for node in emoji_nodes:
            emoji_url     = node.attrib['cdnurl'].replace('http*#*//', 'http://').strip()
            emoji_thumb   = '' if not 'thumburl' in node.attrib else node.attrib['thumburl'].strip()
            emoji_encrypt = '' if not 'encrypturl' in node.attrib else node.attrib['encrypturl'].strip()
            emoji_aeskey  = '' if not 'aeskey' in node.attrib else node.attrib['aeskey'].strip()
            
            emoji['url'] = emoji_url
            emoji['thumb'] = emoji_thumb
            emoji['encrypt'] = emoji_encrypt
            emoji['aeskey'] = emoji_aeskey
            
            msg['content'] = 'EMOJI URL : %s' % (emoji['url'])
            msg['data'] = emoji
            msg['type'] = 'emoji'
            break
            
        appmsg_nodes = doc.xpath('//appmsg')
        if len(appmsg_nodes)>0:
            appmsg['title']         = '' if len(doc.xpath('//title'))==0 else doc.xpath('//title')[0].text.strip()                          
            appmsg['desc']          = '' if len(doc.xpath('//des'))==0 else doc.xpath('//des')[0].text.strip()
            appmsg['url']           = '' if len(doc.xpath('//url'))==0 else doc.xpath('//url')[0].text.strip()                    
            appmsg['sourceuser']    = '' if len(doc.xpath('//sourceusername'))==0 else doc.xpath('//sourceusername')[0].text.strip()
            appmsg['sourcedisplay'] = '' if len(doc.xpath('//sourcedisplayname'))==0 else doc.xpath('//sourcedisplayname')[0].text.strip()
            appmsg['fromuser']      = '' if len(doc.xpath('//fromusername'))==0 else doc.xpath('//fromusername')[0].text.strip()
            appmsg['fromdisplay']   = '' if self.findUser(appmsg['fromuser']) == None else self.findUser(appmsg['fromuser'])['nick'] 
            
            msg['content'] = 'Title   : %s\nSource  : %s\nOriginal: %s [%s]\nForward : %s [%s]\n%s\n%s' % (appmsg['title'], appmsg['url'], appmsg['sourcedisplay'], appmsg['sourceuser'], appmsg['fromdisplay'], appmsg['fromuser'], '-'*80, appmsg['desc'])
            msg['data'] = appmsg
            msg['type'] = 'appmsg'
            
        img_nodes = doc.xpath('//img')
        for node in img_nodes:
            node = img_nodes[0]
            image['aeskey'] = '' if not 'aeskey' in node.attrib else node.attrib['asekey'].strip()
            image['encryver'] = '' if not 'encryver' in node.attrib else node.attrib['encryver'].strip()

            break

        # print(msg_content)
        return(msg)
            
    def showMessage(self, user):
        self.ui_main.tvMessage.clear()
        self.ui_main.tvMessage.setHeaderLabels(['Time', 'Talker', 'Content'])
        # self.ui_main.tvMessage.setMinimumWidth(10)
        # print(self.ui_main.tvMessage.sizeHintForColumn(0)) 
        # headerItem = self.ui_main.tvMessage.headerItem()
        # headerItem.setSizeHint(0, QSize(20, 22)) 

        msgs = getMessages(self.file_db, user, decrypted=self.decrypted, key=self.key)
        id = 0
        for msg in msgs:
            id += 1
            msg_userid  = msg['userid']
            msg_time    = msg['time']
            msg_talker  = msg['talker']

            talker = self.findUser(msg_talker)
            
            msg_tremark = talker['remark'] if talker else ''
            msg_tnick   = talker['nick'] if talker else ''
            msg_talias  = talker['alias'] if talker else ''
                                                    
            msg_content = '' if msg['content'] == None else '\n'.join(msg['content'].strip().split())
            # if id<=5: print(repr(msg_content))
            # if id<=5: print(msg_content)
            try:
                if msg_talker != '我':
                    msg_talker = msg_tremark if msg_tremark else msg_tnick 
                    if msg_userid.endswith('@chatroom'):
                        msg_lines = self.replaceUserId(msg_content).split()
                        if len(msg_lines)>1: 
                            idx = msg_lines[0].find(':')
                            if idx >= 0:                       
                                msg_talker = msg_lines[0][:idx]
                            msg_content = '\n'.join(msg_lines[1:])
                        else:                
                            msg_content = '\n'.join(msg_lines)
                    else:
                        msg_content = '\n'.join(self.replaceUserId(msg_content).split())

                    user = self.findUser(msg_talker)
                    talker_nick   = user['nick'] if user else msg_tnick 
                    talker_alias  = user['alias'] if user else msg_talias
                    talker_remark = user['remark'] if user else msg_tremark
                    if talker_remark :  msg_talker = talker_remark
                    elif talker_alias : msg_talker = talker_alias
                    else:               msg_talker = talker_nick  
                    msg_talker = u'%s' % (msg_talker)
                    msg_tremark = talker_remark
                    msg_tnick = talker_nick
                else:
                    msg_content = self.replaceUserId(msg_content)
            except:
                pass

            msg_tip = msg_content

            try:    
                msgInfo = self.formatMessage(msg_content)
                if msgInfo['type'] == 'emoji':
                    msg_content = msgInfo['content']
                elif msgInfo['type'] == 'appmsg':
                    msg_content = msgInfo['content']
                elif msgInfo['type'] == 'image':
                    msg_content = msgInfo['content']
                elif msgInfo['type'] == 'text':
                    msg_content = msgInfo['content']
            except:
                # print('not xml!')
                pass

                
                
            item_msg = QTreeWidgetItem(self.ui_main.tvMessage)
            item_msg.setText(0, msg_time)
            item_msg.setText(1, msg_talker)
            item_msg.setText(2, '\n' + msg_content + '\n')
                        
            item_msg.setToolTip(0, msg_time)
            item_msg.setToolTip(1, msg_tnick)
            item_msg.setToolTip(2, msg_tip)

        
        self.ui_main.setWindowTitle('%s - %d Messages' % (self.TITLE, id))        

        pass
        
    pass
    
    
    
if __name__ == '__main__':
    # Get database/IMEI from command line
    imei = sys.argv[1]

    # print(QtGui.QTextCursor.End)
    app = QtGui.QApplication(sys.argv)

    # load zh_CN locale
    locale = QtCore.QLocale.system()

    translator_qt = QtCore.QTranslator()
    folder_qt = os.path.dirname(QtCore.__file__)
    translator_qt.load(locale, 'qt', prefix='_', directory = os.path.join(folder_qt, 'translations'), suffix='.qm')
    app.installTranslator(translator_qt)

    filename_app = os.path.splitext(os.path.basename(SCRIPTNAME))[0]
    folder_app = os.path.join(CWD, 'i18n')
    translator_app = QtCore.QTranslator()
    translator_app.load(locale, filename_app, prefix='_', directory = folder_app, suffix='.qm')
    app.installTranslator(translator_app)

    win = WeChatMsgWindow(imei=imei)

    # if sys.stdout.isatty():
    #     pass
    # else:
    #     sys.stdout = OutLog(win.ui_main.edOutput, win, sys.stdout)
    #     sys.stderr = OutLog(win.ui_main.edOutput, win, sys.stderr, QtGui.QColor(255,0,0))

    sys.exit(app.exec_())
        
