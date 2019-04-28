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
from bdp_property import BDPProperty

class BDPAuth():
    def auth(self, username, password):
        if not (username and password):
            return False
        return username == BDPProperty.getInstance().getValue('gateway_user') and password == BDPProperty.getInstance().getValue('gateway_password')

