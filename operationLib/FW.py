
from NetworkDevice import NetworkDevice
import os

class FW(NetworkDevice):
    
    Data_Directory = 'NetworkDevices-Data/FWs'
    
    def Create_Data_Folder(self):
        self.DATA_PATH = FW.Data_Directory+self.DeviceName
        if not os.path.exists(self.DATA_PATH):
            os.makedirs(self.DATA_PATH)
