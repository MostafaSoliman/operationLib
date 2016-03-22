from FW import FW
from netmiko import ConnectHandler
import re
from NetOp import *
from CiscoConfigFW import *
from IP import *
from netaddr import IPNetwork
import random
import os.path


class CISCO(FW):
    #THIS CLASS FOR CISCO ASA/FWSM
    #
    #
    Data_Directory = '/CISCO/'
    FW.Data_Directory += Data_Directory
    
    CMDs = ['show run object-group icmp-type','show run object-group protocol',
            'show run access-group','show run name','show route','show access-list',
            'show time-range','show run object-group network','show run object-group service']
    
    def Get_Device_Info(self):
        result =  self.Update_Device_Data(C=['show version'])[0]
        if 'Cisco Adaptive Security Appliance ' in result:
           #print result 
           self.DeviceType = 'ASA'
           soft_version = re.findall('.+Software\sVersion\s(\d+\.\d+)',result)
           self.DeviceSoftVersion = float(soft_version[0])
           
        elif 'FWSM Firewall' in result:
           self.DeviceType = 'FWSM'
           soft_version = re.findall('.+Firewall\sVersion\s(\d+\.\d+)',result)
           self.DeviceSoftVersion = float(soft_version[0])
        else:
            #
            # TO DO RISE CUSTOM ERROR
            #
            print 'Cannot define device type'
            return False

    def Create_Data_Folders():
        pass

    def Set_High_CPU(self,cpu):
        
        self.HIGH_CPU = cpu
        
    def Get_CPU_Usage(self):
        output = self.net_connect.send_command('show cpu')
        CPUsge=int(re.match('CPU utilization for 5 seconds =\s(\d+)',output).group(1))
        return CPUsge
    
    def Config_Handler(self):
        if not self.ConfigHandler:
            self.ConfigHandler =  CiscoConfigFW(self.DeviceName)
        return self.ConfigHandler
    
    def Open_SSH_Session(self):
        #
        #RETURN CONNECTION HANDLER FOR CISCO DEVICE ,
        #I WILL USE NETMIKO AS IT DOES A GOOD JOB
        #
            
        self.net_connect = ConnectHandler(device_type='cisco_asa', ip=self.DeviceManIp, username=self.username, password=self.password,secret=self.password,verbose=False)
        if self.DEBUG:
            print 'Session Started'
        return self.net_connect

    def Close_SSH_Session(self):
        self.net_connect.disconnect()
        if self.DEBUG:
            print 'Session Closed'
        
    def Check_Device_Data_Exist(self):
        CMDs = CISCO.CMDs
        if self.DeviceType == 'ASA' and self.DeviceSoftVersion > 8.2:
            #ADD MORE COMMANDS NEEDED AND AVALIABLE FOR CERTAIN VERSIONS
            #CMDs.append('show run object network') #TO AVOID SUPNETTING WHEN WE CAN ADD RANGE
            CMDs.append('show run object network')
            CMDs.append('show run object service')
        path = 'NetworkDevices-Data\\FWs\\CISCO\\'+self.DeviceName+'\\'
        Exist = True
        for c in CMDs:
            if not os.path.isfile(path+c+'.txt'):
                if self.DEBUG:
                    print path+c+'.txt' ,'not found'
                Exist = False
        return Exist

        
    def Update_Device_Data(self,C=[]):
        #
        #DOWNLOAD DATA FILES FROM DEVICE
        #SHOULD RETURN LIST OF UNDONE COMMANDS
        #
        CMDs = []
        if C:
            CMDs = C
            Results = []
        else:
            CMDs = CISCO.CMDs        
        
            if self.DeviceType == 'ASA' and self.DeviceSoftVersion > 8.2:
                #ADD MORE COMMANDS NEEDED AND AVALIABLE FOR CERTAIN VERSIONS
                #CMDs.append('show run object network') #TO AVOID SUPNETTING WHEN WE CAN ADD RANGE
                CMDs.append('show run object network')
                CMDs.append('show run object service')
            
        

        if self.DEBUG:
            for c in CMDs:
                print c
        
        self.net_connect = self.Open_SSH_Session()                    
        self.net_connect.enable()
        self.net_connect.send_command("terminal pager 0")

        for cmd in CMDs:
            if self.DEBUG:
                print 'Applyind',cmd
            output = self.net_connect.send_command(cmd,max_loops=200)
            output = Check_Subnets_Errors(output)
            if C:
                Results.append(output)
            else:    
                f=open(self.DATA_PATH+'/'+cmd+'.txt','w')
                f.write(output)
                f.close
        if C:
            return Results
            
    def Get_Interface(self,Network=None):
        #
        # return RoutingConfig object for the route entry lead to input Network
        #
        Interface=[]
        NetmaskList=[]
        ADList=[]
        MetricList=[]
        
        if not self.ConfigHandler:
            self.ConfigHandler =  CiscoConfigFW(self.DeviceName)
        if not self.RoutingHandler  :
            self.RoutingHandler = self.ConfigHandler.RoutingInfo()
        if Network:
            for routeEntryObj in self.RoutingHandler:
                if Check_Network_in_Network(Network,routeEntryObj.DestNetwork):
                    
                    Interface.append(routeEntryObj)
                    NetmaskList.append(routeEntryObj.DestNetwork.split('/')[1])
                    ADList.append(routeEntryObj.AD)
                    MetricList.append(routeEntryObj.Metric)
            if not NetmaskList and not ADList and not MetricList: # incase fw has no default route
                #
                #TO DO : CUSTOM EXCEPTION
                #
                return False
            
            BestIndex=Best_Route(NetmaskList,ADList,MetricList)
            return Interface[BestIndex]
        else:
            return self.RoutingHandler
            
    def Get_ACL_Name(self,NameIf):
        if not self.ConfigHandler:
            self.ConfigHandler =  CiscoConfigFW(self.DeviceName)
        self.ConfigHandler.ObjName = NameIf
        return self.ConfigHandler.ACL_Name()
          
    def Get_Network_IP(self,NetworkName):
        if not self.ConfigHandler:
            self.ConfigHandler =  CiscoConfigFW(self.DeviceName)
        self.ConfigHandler.ObjName = NetworkName
        return self.ConfigHandler.Network_Name_To_IP()
        
    def Get_Network_Objects(self):
        #RETURN ALL NETWORK OBJECTS
        if  self.DeviceType == 'ASA' and self.DeviceSoftVersion > 8.2:
            if not self.ConfigHandler:
                self.ConfigHandler =  CiscoConfigFW(self.DeviceName)
            self.ConfigHandler.ObjName = ''
            Network_Objects = self.ConfigHandler.Network_Objects()
            return Network_Objects
            
            
            
                    
        else:
            pass
            #
            #TO DO : RISE CUSTOM EXCEPTION
            #

            
    def Get_Network_Objects_By_Name(self,Name):
        #RETURN Name NETWOK OBJECT
        if  self.DeviceType == 'ASA' and self.DeviceSoftVersion > 8.2:
            if not self.ConfigHandler:
                self.ConfigHandler =  CiscoConfigFW(self.DeviceName)
            self.ConfigHandler.ObjName = Name
            return  self.ConfigHandler.Network_Objects()

           
        else:
            pass
            #
            #TO DO : RISE CUSTOM EXCEPTION
            #                
    def Get_Network_Objects_By_Type(self,Name):
        if  self.DeviceType == 'ASA' and self.DeviceSoftVersion > 8.2:
            if not self.ConfigHandler:
                self.ConfigHandler =  CiscoConfigFW(self.DeviceName)
            self.ConfigHandler.ObjName = ''
            self.Network_Objects = self.ConfigHandler.Network_Objects()
            for NetObj in  self.Network_Objects:
                if NetObj.Type == Type:
                    return NetObj
           
        else:
            pass
            #
            #TO DO : RISE CUSTOM EXCEPTION
            #
    def Get_Service_Object(self):
        if  self.DeviceType == 'ASA' and self.DeviceSoftVersion > 8.2:
            if not self.ConfigHandler:
                self.ConfigHandler =  CiscoConfigFW(self.DeviceName)
            self.ConfigHandler.ObjName = ''
            Service_Object = self.ConfigHandler.Service_Objects()
            return Service_Object
           
        else:
            pass
            #
            #TO DO : RISE CUSTOM EXCEPTION
            #        

    def Get_Network_Object_Group(self):
        if not self.ConfigHandler:
            self.ConfigHandler =  CiscoConfigFW(self.DeviceName)
        self.ConfigHandler.ObjName = ''
        NetworkObjectGroup = self.ConfigHandler.Network_Object_Group()
        return NetworkObjectGroup
    
    def Get_Network_Object_Group_By_Name(self,ObjName):
        if not self.ConfigHandler:
            self.ConfigHandler =  CiscoConfigFW(self.DeviceName,ObjName)
        self.ConfigHandler.ObjName = ObjName
        return  self.ConfigHandler.Network_Object_Group()
           
    def Get_Service_Object_Group(self):
        if not self.ConfigHandler:
            self.ConfigHandler =  CiscoConfigFW(self.DeviceName)
        self.ConfigHandler.ObjName = ''
        return self.ConfigHandler.Service_Object_Group()
    
    def Get_Service_Object_Group_By_Name(self,ObjName):
        if not self.ConfigHandler:
            self.ConfigHandler =  CiscoConfigFW(self.DeviceName,ObjName)
        
        self.ConfigHandler.ObjName = ObjName
        return   self.ConfigHandler.Service_Object_Group()


    def Get_ACLs(self,srcnet=None,dstnet=None,protocol=None,srcport=None,dstport=None,aclname=None,action=None,Type=None):
        
        if not self.ConfigHandler:
            self.ConfigHandler =  CiscoConfigFW(self.DeviceName)
        ACLs =  self.ConfigHandler.ACLs()


        if Type:
            for acl in list(ACLs):
                if acl.Type != Type:
                    ACLs.remove(acl)            
        if aclname:
            for acl in list(ACLs):
                if acl.Name != aclname:
                    ACLs.remove(acl)

        if action:
            for acl in list(ACLs):
                if acl.Action != action:
                    ACLs.remove(acl)            
        if protocol:
            for acl in list(ACLs):
                if type(acl.Protocol).__name__ == 'str':
                    if protocol != acl.Protocol:
                        ACLs.remove(acl)
                elif type(acl.Protocol).__name__ == 'ServiceObject':
                    if protocol != acl.Protocol.Protocol:
                        ACLs.remove(acl)
                elif type(acl.Protocol).__name__ == 'ServiceObjectGroup':
                    for service in  acl.Protocol.Service:
                        found =False
                        if service.Protocol == protocol:
                            found = True
                    if not found:
                        ACLs.remove(acl)
                        
        if srcnet:
            for acl in list(ACLs):
                if type(acl.SrcNet).__name__  == 'IPNetwork':
                    if IPNetwork(srcnet) not in acl.SrcNet:
                        ACLs.remove(acl)
                elif type(acl.SrcNet).__name__  == 'NetworkObject':
                    if IPNetwork(srcnet) not in acl.SrcNet.Network:
                        ACLs.remove(acl)
                elif type(acl.SrcNet).__name__  == 'NetworkObjectGroup':
                    found = False
                    for Network in acl.SrcNet.Network:
                        if type(Network).__name__  == 'IPNetwork':
                            if IPNetwork(srcnet) in Network:
                                found = True
                        elif type(Network).__name__  == 'NetworkObject':
                            if IPNetwork(srcnet) in Network.Network:
                                found = True
                    if not found:
                        ACLs.remove(acl)
        if dstnet:
            for acl in list(ACLs):
                if type(acl.DstNet).__name__  == 'IPNetwork':
                    if IPNetwork(dstnet) not in acl.DstNet:
                        ACLs.remove(acl)
                elif type(acl.DstNet).__name__  == 'NetworkObject':
                    if IPNetwork(dstnet) not in acl.DstNet.Network:
                        ACLs.remove(acl)
                elif type(acl.DstNet).__name__  == 'NetworkObjectGroup':
                    found = False
                    for Network in acl.DstNet.Network:
                        if type(Network).__name__  == 'IPNetwork':
                            if IPNetwork(dstnet) in Network:
                                found = True
                        elif type(Network).__name__  == 'NetworkObject':
                            if IPNetwork(dstnet) in Network.Network:
                                found = True
                    if not found:
                        ACLs.remove(acl)
                        
        if srcport:
            for acl in list(ACLs):
                if type(acl.SrcPort).__name__ == 'ServiceObjectGroup':
                    for service in acl.SrcPort.Service:
                        found = False
                        if  service.Check_Port(srcport):
                            found = True
                    if not found:
                        ACLs.remove(acl)
                        
                elif type(acl.SrcPort).__name__ == 'CiscoPort':
                    if not  acl.SrcPort.Check_Port(srcport):
                        ACLs.remove(acl)
                
        if dstport:
            for acl in list(ACLs):
                if type(acl.DstPort).__name__ == 'ServiceObjectGroup':
                    for service in acl.DstPort.Service:
                        found = False
                        if  service.Check_Port(dstport):
                            found = True
                    if not found:
                        ACLs.remove(acl)
                        
                elif type(acl.DstPort).__name__ == 'CiscoPort':
                    if not  acl.DstPort.Check_Port(dstport):
                        ACLs.remove(acl)
                    
        return   ACLs      


    def Create_Network_Object(self,network,name=None):
        #network = ''
        
        config=''
        if not name:
            name = 'NetObj_'+str(random.randrange(0,100))+'_'+str(random.randrange(0,100))
        config += 'object network '+name+'\n'
        if '-' in network:
            if self.DeviceType == 'ASA' and self.DeviceSoftVersion > 8.2:
                #create range network object
                config+=' range '+network.split('-')[0]+' '+network.split('-')[1]+''
            else:
                return False
                #
                # TO DO : rise custom error
                #
        elif '/' in network :
            net = str(IPNetwork(network).network)
            mask = str(IPNetwork(network).netmask)
            config += ' subnet '+net+' '+mask+''
        else:
            config += ' host '+network+''

        return NetworkObject(config)

    def Create_Network_Object_Group(self,network,name=None):
        #network =[]
        config=''
        if not name:
            name = 'NetObjGrp_'+str(random.randrange(0,100))+'_'+str(random.randrange(0,100))
        config += 'object network '+name+''
        for net in network:
            config +='\n'
            if type(net) == str:
                if '/' in net:
                    n = str(IPNetwork(net).network)
                    mask = str(IPNetwork(net).netmask)                    
                    config +=' network-object '+n+' '+mask+''
                else:
                    config +=' network-object host '+net+''
            elif type(net).__name__ == 'NetworkObject':
                config +=' network-object object '+net.Name+''
            elif type(net).__name__ == 'NetworkObjectGroup':
                config +=' group-object '+net.Name+''
        return NetworkObjectGroup(config)
                    
    def Create_Service_Object(self,protocol,name=None):
        config=''
        if not name:
            name = 'SrvObj_'+str(random.randrange(0,100))+'_'+str(random.randrange(0,100))
        config += 'object service '+name+'\n'
        
        if type(protocol).__name__ == 'TCPUDP':
            config += ' service '+protocol.Protocol+' source '+protocol.SrcPort.Name+' destination '+protocol.DstPort.Name
            
        elif type(protocol).__name__ ==  'IP':
            config += ' service '+protocol.Protocol
        elif type(protocol).__name__ ==  'ICMP':
            config += ' service '+protocol.Protocol +' '+protocol.ICMPType
        return ServiceObject(config)

    def Create_Service_Object_Group(self,service,name=None):
        config=''
        if not name:
            name = 'SrvObjGrp_'+str(random.randrange(0,100))+'_'+str(random.randrange(0,100))
        config += 'object-group service '+name+''
        for srv in service:
            config += '\n'
            if type(srv).__name__ == 'TCPUDP':
                config += ' service '+srv.Protocol+' source '+srv.SrcPort.Name+' destination '+srv.DstPort.Name
                
            elif type(srv).__name__ ==  'IP':
                config += ' service '+srv.Protocol
            elif type(srv).__name__ ==  'ICMP':
                config += ' service '+srv.Protocol +' '+srv.ICMPType
            elif type(srv).__name__ ==  'ServiceObjectGroup':
                config += ' group-object '+srv.Name            
        return ServiceObjectGroup(config)

    def Create_Port_Object_Group(self,service,protocol,name=None):
        config=''
        if not name:
            name = 'SrvObjGrp_'+str(random.randrange(0,100))+'_'+str(random.randrange(0,100))
        config += 'object-group service '+name+' '+protocol
        for srv in service:
            config += '\n'
            if type(srv).__name__ ==  'CiscoPort':
                config += ' port-object '+srv.Name
            elif type(srv).__name__ ==  'ServiceObjectGroup':
                 config += ' group-object '+srv.Name
        return ServiceObjectGroup(config)                
             
    def Create_ACL(self,Type='extended',lineno='',aclname='',protocol='tcp',srcnet='',dstnet='',srcport='',dstport='',timerange='',action=''):
        if aclname:
            config = 'access-list '+aclname
        else:
            #
            #TO DO RAISE error
            return False
        if lineno:
            config += ' line '+lineno

        config +=' '+Type+' '+action
        if Type == 'extended':
            #protocol
            if type(protocol).__name__ == 'ProtocolObjectGroup':
                config+=' object-group '+protocol.Name
            if type(protocol).__name__ == 'ServiceObjectGroup':
                config+=' object-group '+protocol.Name
            elif type(protocol).__name__ == 'ServiceObject':
                config+=' object '+protocol.Name
            elif type(protocol) == str:
                config+=' '+protocol
            #srcnet
            if type(srcnet).__name__ == 'NetworkObject':
                config+=' object '+srcnet.Name
            elif type(srcnet).__name__ == 'NetworkObjectGroup':
                config+=' object-group '+srcnet.Name
            elif type(srcnet).__name__ == 'IPNetwork':
                net = str(srcnet.network)
                mask = str(srcnet.netmask)
                config+=' '+net+' '+mask
            #srcport
            if type(srcport).__name__ == 'CiscoPort':
                config+=' '+srcport.Name
            elif type(srcport).__name__ == 'ServiceObjectGroup':
                config+=' object-group '+srcport.Name
            #dstnet
            if type(dstnet).__name__ == 'NetworkObject':
                config+=' object '+dstnet.Name
            elif type(dstnet).__name__ == 'NetworkObjectGroup':
                config+=' object-group '+dstnet.Name
            elif type(dstnet).__name__ == 'IPNetwork':
                net = str(dstnet.network)
                mask = str(dstnet.netmask)
                config+=' '+net+' '+mask

            #dstport
            if type(dstport).__name__ == 'CiscoPort':
                config+=' '+dstport.Name
            elif type(dstport).__name__ == 'ServiceObjectGroup':
                config+=' object-group '+dstport.Name

            #timerange
            if timerange:
                config+=' time-range '+timerange
                
        elif Type == 'standard':
            pass
        return ACLs(config)        
            
            

'''        
FW_Dict = { 'FWSM-VAS':'10.204.0.36',
            'F-TAG4-FW1':'10.222.100.1',
            'FWSM_USERS':'172.31.1.1',
            'SERVERS':'172.31.1.70',
            #'NC_FWSM':'10.203.0.195',
            'Outside':'10.199.2.3',
            'CRM':'10.198.3.1',
            'Maadi':'10.194.254.2',
            #'FW-SV-BACKEND':'172.31.3.229'
            }


fw=CISCO('SERVERS',DeviceType='FWSM',DeviceSoftVersion=8.6)
fw.Config_Handler().Initiate_Config()
for acl in fw.Get_ACLs(Type = 'extended',srcnet='10.196.1.158',aclname='W_Apps_In'):
    print acl.config
    pass

service = []
p = ICMP(ICMPType='2')
src = CiscoPort('gt','0','tcp')
dst = CiscoPort('range','80-90','tcp')
c = TCPUDP('tcp',src,dst)
service = [src,dst]
print fw.Create_ACL(Type='extended',lineno='1',aclname='U_MGMNT_P_access_in',protocol='tcp',srcnet=IPNetwork('1.1.1.1/32'),dstnet=IPNetwork('1.1.1.1/32')
                    ,srcport='',dstport=dst,timerange='10-mar-2016',action='permit').config


for route in  fw.Get_Interface():
    print route.DestNetwork,route

print fw.Get_ACL_Name('W_BO_APP').ACL
#print fw.Get_Network_IP('Video_Conference_Tag_4').IP
print fw.Get_Network_Objects_By_Name('10.195.2.76-80').Network
print fw.Get_Service_Object()
#print fw.Get_Service_Object_Group()

for x in fw.Get_Service_Object_Group_By_Name('CRM_NBA_ports1').Service:
    print x.Name



for fwName in FW_Dict:
    fw=CISCO(fwName,FW_Dict[fwName])


    fw.Get_Device_Info()
    print 'device type',fw.DeviceType 
    print 'software version',fw.DeviceSoftVersion
    fw.Update_Device_Data()

    fw.Config_Handler().Initiate_Config()
    for acl in fw.Get_ACLs(Type = 'standard'):
        print acl.config
        pass
'''

