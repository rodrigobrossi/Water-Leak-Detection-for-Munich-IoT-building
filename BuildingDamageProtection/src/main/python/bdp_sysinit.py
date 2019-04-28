#############################################################
# IBM Confidential
# OCO Source Materials
#
#  (C) Copyright IBM Corp. 2019
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has
# been deposited with the U.S. Copyright Office.
#############################################################
import pprint
from bdp_dbutil import *
import ibm_db

from xml.dom import minidom

class BDPSysInit():
    def init(self):
        # Define our connection string
        conn = BDPDBConnection.getInstance().getDBConnection()
        
        sql = "SELECT  * FROM  SYSIBM.SYSTABLES WHERE  type = 'T' AND NAME LIKE 'BDP_%'"
        stmt = ibm_db.exec_immediate(conn, sql)
        records = ibm_db.fetch_both(stmt)
        rownum = 0
        # retrieve the records from the database
        if records != False:
            rownum = len(records.keys())
        
        # print out the records using pretty print
        # note that the NAMES of the columns are not shown, instead just indexes.
        # for most people this isn't very useful so we'll show you how to return
        # columns as a dictionary (hash) in the next example.
        print("BDP tables: " + str(rownum))
        if rownum == 0:
            f = open("resources/db/db2/init.sql", "r")
            flines = f.readlines()
            command = ''
            for line in flines:
                line = line.replace("DBUSER", BDPProperty.getInstance().getValue('db_admin_user'))
                command = command + " " + line.strip()
                if command.endswith(';'):
                    print(command)
                    ibm_db.exec_immediate(conn, command)
                    command = ''
        
        xmldoc = minidom.parse('resources/db/db2/db.changelog.xml')
        itemlist = xmldoc.getElementsByTagName('include')
        print(len(itemlist))
        for s in itemlist:
            filename = s.attributes['file'].value
            print(filename)
            id = filename.split('/')[-1].split('.')[0].split('_')[0]
            #query id
            idnum = 0
            if rownum > 0:
                sql_string = "select * from " + BDPProperty.getInstance().getValue('db_admin_user') + ".BDP_DBCHANGELOG where changeid = '" + id + "'"
                print(sql_string)
                stmt = ibm_db.exec_immediate(conn, sql_string)
                records = ibm_db.fetch_both(stmt)
                if records != False:
                    idnum = 1
            #if id exists, move on to next file
            #otherwise, execute and insert
            if idnum == 0:
                f = open(filename, "r")
                flines = f.readlines()
                command = ''
                for line in flines:
                    line = line.replace("DBUSER", BDPProperty.getInstance().getValue('db_admin_user'))
                    command = command + " " + line.strip()
                    if command.endswith(';'):
                        print(command)
                        ibm_db.exec_immediate(conn, command)
                        command = ''
                    
                sql_string = "insert into " + BDPProperty.getInstance().getValue('db_admin_user') + ".BDP_DBCHANGELOG (changeid, changeset) values ('" + id + "', '" + filename + "')";
                print(sql_string)
                ibm_db.exec_immediate(conn, sql_string)

