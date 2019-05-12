https://github.ibm.com/Watson-IoT/Water-Leak-Detection-for-Munich-IoT-building
https://waterleakdetector.eu-de.mybluemix.net/
https://waterleakdetector.eu-de.mybluemix.net/red/#flow/5fadb76d.41fea8


ibmcloud api https://api.eu-de.bluemix.net
ibmcloud login -u cyjiang@us.ibm.com -o john.d.vasquez@ibm.com -s GermanyDev --sso
cf target -s GermanyDev
ibmcloud app push BuildingDamageProtection
ibmcloud cf logs BuildingDamageProtection
https://bdp.eu-de.mybluemix.net
