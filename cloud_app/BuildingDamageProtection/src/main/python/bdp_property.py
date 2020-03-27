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
import json, os

class BDPProperty():
    __instance = None

    @staticmethod
    def getInstance():
        if BDPProperty.__instance == None:
            BDPProperty()
        return BDPProperty.__instance 

    def __init__(self):
        if BDPProperty.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            BDPProperty.__instance = self
            dirname = os.path.dirname(__file__)
            confpath = os.path.join(dirname, '../../../resources/config/config.json')
            with open(confpath) as f:
                self.data = json.load(f)
                print(self.data)
            
            
            
    def getValue(self, key):
        return self.data[key]

