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
import json

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
            with open('resources/config/config.json') as f:
#            with open('resources/config/ai_task_manager_config_local.json') as f:
                self.data = json.load(f)
                print(self.data)
            
            
            
    def getValue(self, key):
        return self.data[key]

