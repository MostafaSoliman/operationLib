import os


##
#this class for general network device
#contain general methods that are avaliable for all network devices
#such as routing
#


class NetworkDevice(object):
    
    #class variables
    CMDs = [] #variable contain all required commands needed for data collection
    
    def __init__(self,DeviceName,DeviceManIp=None,DeviceType=None,DeviceSoftVersion=None,username='',password=''):
        self.DeviceName = DeviceName
        self.DeviceManIp = DeviceManIp
        self.DeviceType = DeviceType
        self.username = username
        self.password = password
        self.DEBUG = False
        
        self.DeviceSoftVersion = DeviceSoftVersion
        self.Create_Data_Folder()

        self.RoutingHandler = '' #handler for the routing table of the device conatin object map all routes known by the device
        self.ConfigHandler = ''  #handeler to all the device config files
    def Create_Data_Folder(self):
        pass        

    def Update_Device_Data(self,DataLocation = '',C=[]):
        self.DataLocation = DataLocation
        if C:
            CMDs = C
        #will be defined in inheritant classes
        pass

    def Set_Credentials(self,username,password):
        self.username = username
        self.password = password
        
        
        
