import json

class BDPWorktask:

    def __init__(self, urgency, sensor_id, location, humidity_level, link):
        self = {}
        self['spi:action'] = 'Activate'
        self['spi:triTaskTypeCL'] = 'Corrective'
        self['spi_wm:wopriority'] = 'Emergency'
        self['spi:triCurrencyUO'] = 'Euro'  
        self['dcterms:title'] = 'Water Intusion Detected!'
        self['dcterms:description'] = 'Water has been detected! \n Urgency: ' + str(urgency) + '\n Sensor ID: ' + str(sensor_id) + '\n Location: ' + str(location) + '\n Humidity level: ' + str(humidity_level) + '\n See the link for more information: ' + str(link)