class CONFIG(object):

    pass




class ConfigElement(object):

    def __init__(self,ConfigEntry=None,DeviceName='',NeededObject=None):
        
        self.config = ConfigEntry
        self.DeviceName = DeviceName
        self.NeededObject = NeededObject
        #if ConfigEntry:
        self.parse()
