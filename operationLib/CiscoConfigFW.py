import re
from netaddr import IPNetwork,IPRange
from NetOp import *
from IP import CiscoPort,TCPUDP,ICMP,IP
from Config import *


IP_NETMASK_REX = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
IP_REX = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'


class CiscoConfigFW(CONFIG):
    ############################################
    #THIS CLASS PARSE ALL CISCO FW CONFIG FILES#
    ############################################
    #EACH METHODE RETURN LIST OF RoutingConfig OBJECTS FOR DIFFERENT CONFIG TYPE
    #OR CERTIAN CONFIG OBJECT DEFINED BY ObjName
    #
    #


    #
    #TO DO : CUSTOM EXCEPTION FOR UNLOCATED DATA FILE
    #
    def __init__(self,FWName,ObjName=''):
        self.FWName = FWName
        self.ObjName = ObjName
        self.Initiate_Config()


    def Initiate_Config(self):
        self.ACL_Name()
        self.Network_Name_To_IP()
        self.Network_Objects()
        self.Service_Objects()
        self.Network_Object_Group()
        self.Service_Object_Group()
        self.Protocol_Object_Group()
        self.ICMP_TYPE_Object_Group()

    def Clear_Nested_Service_Object_Group(self):
        
        while True:
            Nested = False
            for name,obj in self.Service_Object_Group_Dict.iteritems():
                for subObj in list(obj.Service):
                    if type(subObj) == str:
                        obj.Service.remove(subObj)

                        try:
                            obj.Service += self.Service_Object_Group_Dict[subObj].Service
                        except:
                            obj.Service.append( self.Service_Object_Dict[subObj].ServiceGroup)
                            
                        Nested = True
            if not Nested:
                break
            
    def Clear_Nested_Network_Object_Group(self):
        
        while True:
            Nested = False
            for name,obj in self.Network_Object_Group_Dict.iteritems():
                for subObj in list(obj.Network):
                    if type(subObj) == str:

                        obj.Network.remove(subObj)

                        try:
                            obj.Network += self.Network_Object_Group_Dict[subObj].Network
                        except:
                            obj.Network.append( self.Network_Object_Dict[subObj].Network)
                            
                        Nested = True
            if not Nested:
                break                        
                        
    def RoutingInfo(self):
        #return list of RoutingConfig instance
        fp=open('NetworkDevices-Data/FWs/CISCO/'+self.FWName+'/show route.txt','r')
        output=fp.read()
        fp.close()

        ConfigLines=[]
        self.RoutingEntries =[] #LIST OF RoutingConfig OBJECTS
        for Element in output.split('\n'):
            if Element:
                if(re.match(".*\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*",Element)):  #only choise lines with ip/mask
                    ConfigLines.append(Element)
                    #CHECK IF NEXT LINE RELATED TO CURRENT CONFIG MODE
                    Index = output.split('\n').index(Element)
                    #LAST ELEMENT
                    if Index == len(output.split('\n')) - 1:
                        self.RoutingEntries.append(RoutingConfig(ConfigLines[-1]))
                        continue
                        
                    NextElement = output.split('\n')[Index+1]
                    if re.match(".*\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*",NextElement):
                        self.RoutingEntries.append(RoutingConfig(ConfigLines[-1]))
                    else:
                        continue
                        
                        
                elif (re.match("\[(\d+/\d+)\]",Element.split()[0])):
                    ConfigLines[-1]+='\n'+Element
                    #CHECK IF NEXT LINE RELATED TO CURRENT CONFIG MODE
                    Index = output.split('\n').index(Element)
                    #LAST ELEMENT
                    if Index == len(output.split('\n')) -1:
                        self.RoutingEntries.append(RoutingConfig(ConfigLines[-1]))
                        continue                
                    NextElement = output.split('\n')[Index+1]
                    if re.match(".*\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*",NextElement):
                        self.RoutingEntries.append(RoutingConfig(ConfigLines[-1]))
                    else:
                        continue
        return self.RoutingEntries
    
    def ACL_Name(self):
        """
            RETURN ALL ACCESS-GROUP OBJECT OR ACCESS GROUP OBJECT OF MENTIONED INTERFACE
        """
        
        fp=open('NetworkDevices-Data/FWs/CISCO/'+self.FWName+'/show run access-group.txt','r')
        output=fp.read()
        fp.close()
        
            
        self.Access_Group_Dict = {}
        for line in output.split('\n'):
            if line:
                InterfaceObj = AccessGroupConfig(line)
                self.Access_Group_Dict[InterfaceObj.Interface]=InterfaceObj
                '''
                if InterfaceName:
                    if InterfaceObj.Interface == InterfaceName:
                        return InterfaceObj
                else:    
                    self.Access_Group_Entries.append(InterfaceObj)
                '''
        if self.ObjName:
            return self.Access_Group_Dict[self.ObjName]
        return self.Access_Group_Dict
            
            
            
    def Network_Name_To_IP(self):
        #print 'reading names'
        fp=open('NetworkDevices-Data/FWs/CISCO/'+self.FWName+'/show run name.txt','r')
        output=fp.read()
        fp.close()
        self.Network_Name_IP_Dict= {}
        
        
        for line in output.split('\n'):
            if line:
                NetToIPObj = NetworkName(line)
                self.Network_Name_IP_Dict[NetToIPObj.Name] = NetToIPObj
                '''
                if NetName:
                    if NetToIPObj.Name == NetName:
                        return NetToIPObj
                else:
                    self.Network_Name_IP_Dict[NetToIPObj.Name] = NetToIPObj
                '''
        if self.ObjName:
            return self.Network_Name_IP_Dict[self.ObjName]
        return self.Network_Name_IP_Dict

    
    def Network_Objects(self):
        try:
            fp=open('NetworkDevices-Data/FWs/CISCO/'+self.FWName+'/show run object network.txt','r')
            output=fp.read()
            fp.close()
        except:
            self.Network_Object_Dict = {}
            return False
        ObjConf=''
        self.Network_Object_Dict={}
        NetName = self.ObjName
        for line in output.split('\n'):
            if line:
                if 'object' == line.split()[0]:
                    ObjConf=''
                    ObjConf+=line
                elif ' ' == line[0]:
                    ObjConf+='\n'+line

                Index = output.split('\n').index(line)
                if Index == len(output.split('\n')) - 1:#last line
                    NetObj = NetworkObject(ObjConf,NeededObject=[self.Network_Name_IP_Dict])
                    self.Network_Object_Dict[NetObj.Name] = NetObj
                    '''
                    if NetName:
                        if NetName == NetObj.Name:
                            return NetObj
                    else:
                        self.Network_Object_Dict[NetObj.Name] = NetObj
                    '''
                                                 
                    continue
                NextLine = output.split('\n')[Index+1]
                if NextLine:
                    if ' ' !=NextLine[0]:
                        NetObj = NetworkObject(ObjConf,NeededObject=[self.Network_Name_IP_Dict])
                        self.Network_Object_Dict[NetObj.Name] = NetObj
                        '''
                        if NetName:
                            if NetName == NetObj.Name:
                                return NetObj
                        else:
                            self.Network_Object_Dict[NetObj.Name] = NetObj
                        '''
        if self.ObjName:
            return self.Network_Object_Dict[self.ObjName]                            
        return self.Network_Object_Dict
                
    def Service_Objects(self):
        try:
            fp=open('NetworkDevices-Data/FWs/CISCO/'+self.FWName+'/show run object service.txt','r')
            output=fp.read()
            fp.close()
        except:
            self.Service_Object_Dict = {}
            return False
        ObjConf=''
        self.Service_Object_Dict={}
        ServName = self.ObjName
        for line in output.split('\n'):
            if line:
                if 'object' == line.split()[0]:
                    ObjConf=''
                    ObjConf+=line
                elif ' ' == line[0]:
                    ObjConf+='\n'+line

                Index = output.split('\n').index(line)
                if Index == len(output.split('\n')) - 1:
                    SrvObj = ServiceObject(ObjConf)
                    self.Service_Object_Dict[SrvObj.Name] = SrvObj
                    '''
                    if ServName:
                        if ServName == SrvObj.Name:
                            return SrvObj
                    else:
                        
                        self.Service_Object_Dict[SrvObj.Name] = SrvObj
                    '''
                    continue
                NextLine = output.split('\n')[Index+1]
                if NextLine:
                    if ' ' !=NextLine[0]:
                        SrvObj = ServiceObject(ObjConf)
                        self.Service_Object_Dict[SrvObj.Name] = SrvObj
                        '''
                        if ServName:
                            if ServName == SrvObj.Name:
                                return SrvObj
                        else:
                            
                            self.Service_Object_Dict[SrvObj.Name] = SrvObj
                        '''
        if self.ObjName:
            return self.Service_Object_Dict[self.ObjName]                             
        return self.Service_Object_Dict
                                
    def Network_Object_Group(self):
        fp=open('NetworkDevices-Data/FWs/CISCO/'+self.FWName+'/show run object-group network.txt','r')
        output=fp.read()
        fp.close()
        ObjConf=''        
        self.Network_Object_Group_Dict={}
        Lines = output.split('\n')
        for i in range(len(Lines)) :
            if Lines[i]:
                if 'object-group' == Lines[i].split()[0]:
                    ObjConf=''
                    ObjConf+=Lines[i]
                elif ' ' == Lines[i][0]:
                    ObjConf+='\n'+Lines[i]

                
                if i == len(output.split('\n')) - 1:
                    NetObj = NetworkObjectGroup(ObjConf,self.FWName,NeededObject=[self.Network_Name_IP_Dict])
                    '''
                    #replace network object name by its object
                    for i in range(len(NetObj.Network)):
                        if type(NetObj.Network[i]) == str:
                            try:
                                NetObj.Network[i] = self.Network_Object_Dict[NetObj.Network[i]]
                            except:
                                NetObj.Network[i] = self.Network_Object_Group_Dict[NetObj.Network[i]]
                    '''
                                
                    self.Network_Object_Group_Dict[NetObj.Name] =NetObj
                    '''
                    if self.ObjName:
                        
                        if NetObj.Name == self.ObjName:
                            return NetObj
                    else:
                        self.Network_Object_Group_Dict[NetObj.Name] =NetObj
                    '''
                    continue
                NextLine = Lines[i+1]
                if NextLine:
                    if ' ' !=NextLine[0]:
                        NetObj = NetworkObjectGroup(ObjConf,self.FWName,NeededObject=[self.Network_Name_IP_Dict])
                        '''
                        #replace network object name by its object
                        for i in range(len(NetObj.Network)):
                            if type(NetObj.Network[i]) == str:
                                try:
                                    NetObj.Network[i] = self.Network_Object_Dict[NetObj.Network[i]]
                                except:
                                    NetObj.Network[i] = self.Network_Object_Group_Dict[NetObj.Network[i]]
                        '''
                        self.Network_Object_Group_Dict[NetObj.Name] =NetObj
                        
                        '''
                        if self.ObjName:
                            
                            if NetObj.Name == self.ObjName:
                                return NetObj
                        else:
                            self.Network_Object_Group_Dict[NetObj.Name] =NetObj
                        '''
        self.Clear_Nested_Network_Object_Group()
        if self.ObjName:
            return self.Network_Object_Group_Dict[self.ObjName]                        
        return self.Network_Object_Group_Dict        
    
    def Service_Object_Group(self):
        fp=open('NetworkDevices-Data/FWs/CISCO/'+self.FWName+'/show run object-group service.txt','r')
        output=fp.read()
        fp.close()
        ObjConf=''        
        self.Service_Object_Group_Dict={}
        Lines = output.split('\n')
        for i in range(len(Lines)) :
            if Lines[i]:
                if 'object-group' == Lines[i].split()[0]:

                    ObjConf=''
                    ObjConf+=Lines[i]
                elif ' ' == Lines[i][0]:
                    ObjConf+='\n'+Lines[i]


                if i == len(output.split('\n')) - 1:

                    SrvObj = ServiceObjectGroup(ObjConf,self.FWName)
                    self.Service_Object_Group_Dict[SrvObj.Name] = SrvObj
                    '''
                    if self.ObjName:
                        
                        if SrvObj.Name == self.ObjName:
                            return SrvObj
                    else:
                        self.Service_Object_Group_Dict[SrvObj.Name] = SrvObj
                    '''
                    continue
                NextLine = Lines[i+1]
                if NextLine:
                    if ' ' !=NextLine[0]:

                        SrvObj = ServiceObjectGroup(ObjConf,self.FWName)
                        self.Service_Object_Group_Dict[SrvObj.Name] = SrvObj
                        '''
                        if self.ObjName:
                            
                            if SrvObj.Name == self.ObjName:
                                return SrvObj
                        else:
                            self.Service_Object_Group_Dict[SrvObj.Name] = SrvObj
                        '''
        self.Clear_Nested_Service_Object_Group()
        if self.ObjName:
            return self.Service_Object_Group_Dict[self.ObjName]
        return self.Service_Object_Group_Dict
    
    def Protocol_Object_Group(self):
        fp=open('NetworkDevices-Data/FWs/CISCO/'+self.FWName+'/show run object-group protocol.txt','r')
        output=fp.read()
        fp.close()
        ObjConf=''        
        self.Protocol_Object_Group_Dict={}
        Lines = output.split('\n')
        
        for i in range(len(Lines)) :
            
            
            if Lines[i]:
                if 'object-group' == Lines[i].split()[0]:

                    ObjConf=''
                    ObjConf+=Lines[i]
                elif ' ' == Lines[i][0]:
                    ObjConf+='\n'+Lines[i]

                if i == (len(Lines) - 1):
                    

                    ProObj = ProtocolObjectGroup(ObjConf,self.FWName)
                    self.Protocol_Object_Group_Dict[ProObj.Name] = ProObj
                    '''
                    if self.ObjName:
                        
                        if ProObj.Name == self.ObjName:
                            return SrvObj
                    else:
                        self.Protocol_Object_Group_Dict[ProObj.Name] = ProObj
                    '''
                    continue
                NextLine = Lines[i+1]
                if NextLine:
                    if ' ' !=NextLine[0]:
                        
                        
                        ProObj = ProtocolObjectGroup(ObjConf,self.FWName)
                        self.Protocol_Object_Group_Dict[ProObj.Name] = ProObj
                        '''
                        if self.ObjName:
                            
                            if ProObj.Name == self.ObjName:
                                return ProObj
                        else:
                            self.Protocol_Object_Group_Dict[ProObj.Name] = ProObj
                        '''
                else:
                    ProObj = ProtocolObjectGroup(ObjConf,self.FWName)
                    self.Protocol_Object_Group_Dict[ProObj.Name] = ProObj

        
        if self.ObjName:
            return self.Protocol_Object_Group_Dict[self.ObjName]                    
        return self.Protocol_Object_Group_Dict


    def ICMP_TYPE_Object_Group(self):
        fp=open('NetworkDevices-Data/FWs/CISCO/'+self.FWName+'/show run object-group icmp-type.txt','r')
        output=fp.read()
        fp.close()
        ObjConf=''        
        self.ICMP_TYPE_Object_Group_Dict={}
        Lines = output.split('\n')
        
        for i in range(len(Lines)) :
            
            
            if Lines[i]:
                if 'object-group' == Lines[i].split()[0]:

                    ObjConf=''
                    ObjConf+=Lines[i]
                elif ' ' == Lines[i][0]:
                    ObjConf+='\n'+Lines[i]

                if i == (len(Lines) - 1):
                    

                    ProObj = ICMPTypeObjectGroup(ObjConf,self.FWName)
                    self.ICMP_TYPE_Object_Group_Dict[ProObj.Name] = ProObj
                    '''
                    if self.ObjName:
                        
                        if ProObj.Name == self.ObjName:
                            return SrvObj
                    else:
                        self.Protocol_Object_Group_Dict[ProObj.Name] = ProObj
                    '''
                    continue
                NextLine = Lines[i+1]
                if NextLine:
                    if ' ' !=NextLine[0]:
                        
                        
                        ProObj = ICMPTypeObjectGroup(ObjConf,self.FWName)
                        self.ICMP_TYPE_Object_Group_Dict[ProObj.Name] = ProObj
                        '''
                        if self.ObjName:
                            
                            if ProObj.Name == self.ObjName:
                                return ProObj
                        else:
                            self.Protocol_Object_Group_Dict[ProObj.Name] = ProObj
                        '''
                else:
                    ProObj = ICMPTypeObjectGroup(ObjConf,self.FWName)
                    self.ICMP_TYPE_Object_Group_Dict[ProObj.Name] = ProObj

        if self.ObjName:
            return self.ICMP_TYPE_Object_Group_Dict[self.ObjName]                    
        return self.ICMP_TYPE_Object_Group_Dict
    
    def ACLs(self):
        """
            RETURN ACL BASSED ON SRCNET DSTNET ACLNAME PORTS PROTOCOL
        """
        fp=open('NetworkDevices-Data/FWs/CISCO/'+self.FWName+'/show access-list.txt','r')
        output=fp.read()
        fp.close()

        self.ACLs_Object_List=[]
        LineNo = ''
        ACLName = ''
        for line in output.split('\n'):
            
            if line:
                if re.match('(0x.+)',line.split()[-1]) and 'name hash' not in line and 'icmp6' not in line: #TAKE ACL LINES ONLY egnore ipv6
                    if 'object' in line.split() or 'object-group' in line.split():
                        LineNo = line.split()[3]
                        ACLName = line.split()[1]
                        ACL_Obj = ACLs(line,self.FWName,[self.Service_Object_Dict,
                                                         self.Service_Object_Group_Dict,
                                                         self.Protocol_Object_Group_Dict,
                                                         self.ICMP_TYPE_Object_Group_Dict,
                                                         self.Network_Name_IP_Dict])
                        #print ACL_Obj.DstNet
                        #print ACL_Obj.SrcNet
                        #print ACL_Obj.DstPort

                        """
                            Remap acl srcnet/dstnet/srport/dstport into objects if the are type str (hold the object name)
                        """
                        if type(ACL_Obj.SrcNet) == str:
                            try:
                                ACL_Obj.SrcNet = self.Network_Object_Dict[ACL_Obj.SrcNet]
                            except:
                                ACL_Obj.SrcNet = self.Network_Object_Group_Dict[ACL_Obj.SrcNet]
                        if type(ACL_Obj.DstNet) == str:
                            try:
                                ACL_Obj.DstNet = self.Network_Object_Dict[ACL_Obj.DstNet]
                            except:
                                ACL_Obj.DstNet = self.Network_Object_Group_Dict[ACL_Obj.DstNet]
                        if type(ACL_Obj.SrcPort) == str:
                            ACL_Obj.SrcPort = self.Service_Object_Group_Dict[ACL_Obj.SrcPort]
                        if type(ACL_Obj.DstPort) == str:
                            ACL_Obj.DstPort = self.Service_Object_Group_Dict[ACL_Obj.DstPort]
                        '''
                        """
                            map all ports to servicegroup 
                        """
                        if ACL_Obj.ServiceGroup: #if its defined
                            if type(ACL_Obj.ServiceGroup) == str:
                                #if ACL_Obj.Protocol == 'tcp' or ACL_Obj.Protocol == 'udp': 
                                try:
                                    ServObj = self.Service_Object_Dict[ACL_Obj.ServiceGroup] #LOOK AT SERVICE OBJECT DICT
                                    if ServObj.Protocol == 'ip':
                                        ACL_Obj.ServiceGroup = IP()
                                    elif ServObj.Protocol == 'icmp':
                                        ACL_Obj.ServiceGroup = ICMP(ICMPType = ServObj.ICMP_Type )
                                    elif ServObj.Protocol == 'tcp' or ServObj.Protocol == 'udp' or ServObj.Protocol == 'tcp-udp':    
                                        ACL_Obj.ServiceGroup = TCPUDP(ServObj.Protocol,ServObj.SrcPort,ServObj.DstPort )
                                except:
                                    try:
                                        ServObj = self.Service_Object_Group_Dict[ACL_Obj.ServiceGroup] #LOOK AT SERVICE OBJECT GROUP DICT 
                                        ACL_Obj.ServiceGroup = ServObj
                                           
                                    except:
                                        try:
                                            ACL_Obj.ServiceGroup = self.Protocol_Object_Group_Dict[ACL_Obj.ServiceGroup] #LOOK AT PROTOCOL OBJECT GROUP DICT
                                            #ACL_Obj.ServiceGroup = None #beacuse we will use the object-group defined at src and dst ports
                                           
                                        except:
                                            if ACL_Obj.Protocol !='icmp':
                                                
                                                #
                                                #TODO RISE CUSTOM EXCEPTION , SHOULD NOT HAPPEN
                                                #
                                                raise NameError
                                            ACL_Obj.ServiceGroup = self.ICMP_TYPE_Object_Group_Dict[ACL_Obj.ServiceGroup] #LOOK AT ICMPType object group
                            
                                           
                            elif type(ACL_Obj.ServiceGroup).__name__ == 'TCPUDP':
                                if type(ACL_Obj.ServiceGroup.SrcPort) == str:
                                    ACL_Obj.ServiceGroup.SrcPort = self.Service_Object_Group_Dict[ACL_Obj.ServiceGroup.SrcPort]
                                if type(ACL_Obj.ServiceGroup.DstPort) == str:
                                    ACL_Obj.ServiceGroup.DstPort = self.Service_Object_Group_Dict[ACL_Obj.ServiceGroup.DstPort]
                            ''' 

                        self.ACLs_Object_List.append(ACL_Obj)        
                        continue
                        
                    if line.split()[3] == LineNo and line.split()[1] == ACLName :
                        continue
                    self.ACLs_Object_List.append(ACLs(line,self.FWName,[self.Network_Name_IP_Dict]))
                    
        return self.ACLs_Object_List         
      
                


class RoutingConfig(ConfigElement):
    def parse(self):
        NumberOfLines = len(self.config.split('\n'))
        self.RouteList =[]
        self.DIRECT_CONNECTED = False
        self.DEFAULT_ROUTE = False
        for line in self.config.split('\n'):
            if ' ' != line[0]:
                self.RouteSource = line.split()[0]
            if '*' in self.RouteSource:
                self.DEFAULT_ROUTE = True                
            
            if(re.match(".*\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*",line)):         
                self.DestNetwork = '/'.join(re.match(".*\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*",line).group(1).split())
            
            if 'via' in line:
                
                if(re.match(".*\s\[(\d+/\d+)\].*",line)):
                    AD=int(re.match(".*\s\[(\d+/\d+)\].*",line).group(1).split('/')[0])
                    Metric=int(re.match(".*\s\[(\d+/\d+)\].*",line).group(1).split('/')[1])
                NextHop=line.split()[line.split().index('via')+1]

                if NextHop[-1]==',':
                    NextHop = NextHop[:-1]
                if not re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',line.split()[-1]):
                    ExitInt = line.split()[-1]
                self.RouteList.append({'AD':AD,'Metric':Metric,'NextHop':NextHop,'ExitInt':ExitInt})
            elif 'directly connected' in line:
                self.DIRECT_CONNECTED = True
                Metric = 0
                AD = 0
                NextHop = 0
                ExitInt = line.split()[-1]
                self.RouteList.append({'AD':AD,'Metric':Metric,'NextHop':NextHop,'ExitInt':ExitInt})
        #MAP object attribute to filrst element in list RouteList
        self.AD =   self.RouteList[0]['AD']  
        self.Metric =   self.RouteList[0]['Metric']                
        self.NextHop =   self.RouteList[0]['NextHop']
        self.ExitInt =   self.RouteList[0]['ExitInt']

        
class AccessGroupConfig(ConfigElement):
    def parse(self):
        self.ACL = self.config.split()[1]
        self.Direction = self.config.split()[2]
        self.Interface = self.config.split()[-1]

class NetworkName(ConfigElement):
    def parse(self):
        self.IP = self.config.split()[1]
        self.Name = self.config.split()[2]
        
class NetworkObject(ConfigElement):
    def parse(self):
        
        self.__name__ = 'NetworkObject'
        if self.NeededObject:
            Network_Name_IP_Dict =  self.NeededObject[0]
        for line in self.config.split('\n'):
            if 'object' == line.split()[0]:
                self.Name = line.split()[2]
            elif 'subnet' == line.split()[0]:
                self.Type = 'subnet'
                if Check_Valid_Netwok(line.split()[1]):
                    self.Network = IPNetwork(line.split()[1]+'/'+line.split()[2])
                else:
                    net = Network_Name_IP_Dict[line.split()[1]].IP
                    self.Network = IPNetwork(net+'/'+line.split()[2])
                    
            elif 'host' == line.split()[0]:
                self.Type = 'host'
                if Check_Valid_Netwok(line.split()[1]):
                    self.Network = IPNetwork(line.split()[1]+'/32')
                else:
                    net = Network_Name_IP_Dict[line.split()[1]].IP
                    self.Network = IPNetwork(net+'/32')                    
            elif 'range' == line.split()[0]:
                self.Type = 'range'
                self.Network = IPRange(line.split()[1],line.split()[2])            

class ServiceObject(ConfigElement):
    """
        CONTAIN SRC PORT DST PORT AND PROTOCOL
        FOR (object service obj_name) COMMAND
    """
    def parse(self):
        
        self.Protocol = None
        ICMP_Type = None
        self.ServiceGroup =None
        
        for line in self.config.split('\n'):
            if 'object' == line.split()[0]:
                
                self.Name = line.split()[2]
            elif 'service' == line.split()[0]:
                
                if 'ip' == line.split()[1]:
                    self.Protocol = 'ip'
                    self.ServiceGroup = IP()
                elif 'icmp' in line.split()[1]:
                    self.Protocol = line.split()[1]
                    ICMP_Type = line.split()[2]
                    if not re.match('\d+',ICMP_Type):
                        ICMP_Type = Get_ICMP_Type(ICMP_Type)                    
                    self.ServiceGroup = ICMP(ICMPType=ICMP_Type)
                    
                elif 'tcp' == line.split()[1] or 'udp' == line.split()[1]:
                    self.Protocol = line.split()[1]
                    if 'source' in line:
                        
                        Index = line.split().index('source')
                         
                        SrcOperator =  line.split()[Index+1]
                        if SrcOperator == 'range':
                            port1 = line.split()[Index+2]
                            if not re.match('\d+',port1):
                                port1 = Get_Port_Number(port1)
                            port2 = line.split()[Index+3]
                            if not re.match('\d+',port2):
                                port2 = Get_Port_Number(port2)
                            SrcPort = CiscoPort(SrcOperator,port1+'-'+port2,self.Protocol)
                        else:
                            port = line.split()[Index+2]
                            if not re.match('\d+',port):
                                port = Get_Port_Number(port)
                            
                            SrcPort = CiscoPort(SrcOperator,port,self.Protocol)                            
                    else:
                        SrcPort = CiscoPort('gt','0',self.Protocol) 
                        

                    if 'destination' in line:
                        
                        Index = line.split().index('destination')
                        
                        DstOperator =  line.split()[Index+1]
                        
                        if DstOperator == 'range':
                            port1 = line.split()[Index+2]
                            if not re.match('\d+',port1):
                                port1 = Get_Port_Number(port1)
                            port2 = line.split()[Index+3]
                            if not re.match('\d+',port2):
                                port2 = Get_Port_Number(port2)                            
                            DstPort =  CiscoPort(DstOperator,port1+'-'+port2,self.Protocol)
                        else:
                            port = line.split()[Index+2]
                            if not re.match('\d+',port):
                                port = Get_Port_Number(port)                            
                            DstPort =  CiscoPort(DstOperator,port,self.Protocol)                            
                    else:
                        DstPort = CiscoPort('gt','0',self.Protocol)
                    self.ServiceGroup = TCPUDP(self.Protocol,SrcPort,DstPort)
                else:
                    self.Protocol = line.split()[1]
                    self.ServiceGroup = IP(self.Protocol)


class NetworkObjectGroup(ConfigElement):
    def parse(self):
        #print self.config
        #print
        if self.NeededObject:
            Network_Name_IP_Dict =  self.NeededObject[0]
        self.Network=[]
        for line in self.config.split('\n'):
            if 'object-group' == line.split()[0]:                
                self.Name = line.split()[2]
            elif 'group-object' == line.split()[0]:
                objName =   line.split()[1]
                self.Network.append(objName)                
            elif 'network-object' == line.split()[0]:
                
                if 'host' == line.split()[1]:
                    if Check_Valid_Netwok(line.split()[2]):
                        self.Network.append(IPNetwork(line.split()[2]+'/32'))
                    else:
                        net = Network_Name_IP_Dict[line.split()[2]].IP
                        self.Network.append(IPNetwork(net+'/32'))
                elif 'object' == line.split()[1]:
                    objName =   line.split()[2]
                    self.Network.append(objName)
                    '''
                    ConfigHandler = CiscoConfigFW(self.DeviceName)
                    NetworkObjList = ConfigHandler.Network_Objects()
                    for NetObj in NetworkObjList:
                        if NetObj.Name == objName:
                            self.Network.append(NetObj)
                    '''
                else:
                    #Network mask
                    if Check_Valid_Netwok(line.split()[1]):
                        self.Network.append(IPNetwork(line.split()[1]+'/'+line.split()[2]))
                    else:
                        net = Network_Name_IP_Dict[line.split()[1]].IP
                        self.Network.append(IPNetwork(net+'/'+line.split()[2]))

class ProtocolObjectGroup(ConfigElement):
    def parse(self):
        self.Protocol=[]
        for line in self.config.split('\n'):
            if 'object-group' == line.split()[0]:                
                self.Name = line.split()[2]            
            elif 'protocol-object' == line.split()[0]:
                self.Protocol.append(line.split()[1])
                

class ServiceObjectGroup(ConfigElement):
    """
    CLASS PARSE SERVICEOBJECTGROUP TO OBJECT WITH THE BELLOW VARIABLES
        Service --> [CiscoPort , str(name for nasted objects) , TCPUDP , IP , ICMP ]
        Type --> 'port/service' PORT OBJECTGROUP THAT IS USED AS SRC/DST PORTS , OR SERVICE OBJECTGROUP THAT IS USED AS PROTOCOL IN ACL.
        Protocol --> INDECATE THE PROTCOL TYPE INCASE port TYPE (TCP/UDP/TCP-UDP) , MEANLESS IN service Type OBJECTGROUP
"""
    
    def parse(self):
        self.Service=[]
        self.Type = '' # port/service
        
        for line in self.config.split('\n'):
            if 'object-group' == line.split()[0]:                
                self.Name = line.split()[2]
                self.Protocol = line.split()[-1]
                if self.Protocol == 'tcp' or self.Protocol == 'udp' or self.Protocol == 'tcp-udp':
                    self.Type = 'port'
                    #self.Protocol = None #SERVICE OBJECT GROUP
                else:
                    self.Type = 'service'
                    
            elif 'group-object' == line.split()[0]:
                self.Service.append(line.split()[1])
                
            elif 'port-object' == line.split()[0]:
                operator = line.split()[1]
                if operator == 'range':
                    port1 = line.split()[2]
                    if not re.match('\d+',port1):
                        port1 = Get_Port_Number(port1)
                    port2 = line.split()[3]
                    if not re.match('\d+',port2):
                        port2 = Get_Port_Number(port2)
                    self.Service.append(CiscoPort(operator,port1+'-'+port2,self.Protocol) )
                else:
                    port = line.split()[2]
                    if not re.match('\d+',port):
                        port = Get_Port_Number(port)
                    self.Service.append(CiscoPort(operator,port,self.Protocol) )
            elif 'service-object' == line.split()[0]:
                Protocol = line.split()[1]
                if Protocol == 'tcp' or Protocol == 'udp' or Protocol == 'tcp-udp':
                    if 'source' in line.split():
                        index = line.split().index('source')
                        operator = line.split()[index+1]
                        if 'range' == operator:
                            port1 = line.split()[index+2]
                            port2 = line.split()[index+3]
                            if not re.match('\d+',port1):
                                port1 = Get_Port_Number(port1)                            
                            if not re.match('\d+',port2):
                                port2 = Get_Port_Number(port2)
                            srcport = CiscoPort(operator,port1+'-'+port2,Protocol)
                        else:
                            
                            srcport = CiscoPort(operator,line.split()[index+2],Protocol)
                    else:
                        srcport = CiscoPort('gt','0',Protocol)
                        
                    if 'destination' in line.split():
                        index = line.split().index('destination')
                        operator = line.split()[index+1]
                        if 'range' == operator:
                            port1 = line.split()[index+2]
                            port2 = line.split()[index+3]
                            if not re.match('\d+',port1):
                                port1 = Get_Port_Number(port1)                            
                            if not re.match('\d+',port2):
                                port2 = Get_Port_Number(port2)
                            dstport = CiscoPort(operator,port1+'-'+port2,Protocol)
                        else:
                            
                            dstport = CiscoPort(operator,line.split()[index+2],Protocol)
                    else:
                        dstport = CiscoPort('gt','0',Protocol)
                    
                    self.Service.append(TCPUDP(Protocol,srcport,dstport) )
                elif Protocol == 'icmp':
                    ICMP_Type = line.split()[2]
                    if not re.match('\d+',ICMP_Type):
                        ICMP_Type=Get_ICMP_Type(ICMP_Type)
                    self.Service.append(ICMP(ICMP_Type))
                elif Protocol == 'ip':
                    self.Service.append(IP())
                elif Protocol == 'object':
                    self.Service.append(line.split()[2])
                else:
                    self.Service.append(IP(Protocol))
                
                #
                #TO DO : NESTED OBJECT
                #
                    


                '''
                if 'eq' == line.split()[1]:
                    port = line.split()[2]
                    if not re.match('\d+',port):
                        port = Get_Port_Number(port) 
                    self.Service.append(int(port))
                elif 'lt' == line.split()[1]:
                    port = line.split()[2]
                    if not re.match('\d+',port):
                        port = Get_Port_Number(port)
                    self.Service += range(int(port)-1,0,-1)
                elif 'gt' == line.split()[1]:
                    port = line.split()[2]
                    if not re.match('\d+',port):
                        port = Get_Port_Number(port)
                    self.Service +=  range(int(port)+1,65536)
                elif 'range' == line.split()[1]:
                    port1 = line.split()[2]
                    if not re.match('\d+',port1):
                        port1 = Get_Port_Number(port1)
                    port2 = line.split()[3]
                    if not re.match('\d+',port2):
                        port2 = Get_Port_Number(port2)
                    self.Service += range(int( port1),int(port2)+1 )
                
                elif 'object':
                    objName =   line.split()[2]
                    ConfigHandler = CiscoConfigFW(self.DeviceName)
                    ServiceObjList = ConfigHandler.Service_Objects()
                    for SrvObj in ServiceObjList:
                        if SrvObj.Name == objName:
                            self.Service.append(SrvObj)                    
                    
                '''
class ICMPTypeObjectGroup(ConfigElement):
    def parse(self):
        self.Service=[]

        
        for line in self.config.split('\n'):
            if 'object-group' == line.split()[0]:                
                self.Name = line.split()[2]
                self.Protocol = 'icmp'
                                
            elif 'icmp-object' == line.split()[0]:
                icmpType = line.split()[1]
                if not re.match('\d+',icmpType):
                    icmpType = Get_ICMP_Type(icmpType)
                self.Service.append(ICMP(icmpType))                
            elif 'group-object' == line.split()[0]:
                self.Service.append(line.split()[1])

        
class ACLs(ConfigElement):

    def parse(self):
        if self.NeededObject:
            if 'object' in self.config.split() or 'object-group' in self.config.split():
                Service_Object_Dict = self.NeededObject[0]
                Service_Object_Group_Dict = self.NeededObject[1]
                Protocol_Object_Group_Dict = self.NeededObject[2]
                ICMP_TYPE_Object_Group_Dict = self.NeededObject[3]
                Network_Name_IP_Dict = self.NeededObject[4]
            else:
                Network_Name_IP_Dict = self.NeededObject[0]
        self.Name=None
        self.Protocol = None
        self.Type = None
        self.Action = None
        self.SrcNet = None
        self.SrcPort = None
        self.DstNet = None
        #self.ServiceGroup = None
        self.DstPort = None
        self.TimeRange = None
        self.LineNo=None
        self.HitCount = None
        self.HexIdent = None
        self.DstICMPType = None
        self.InActive = False
        Index = 7
        self.HitCount = re.match('.+hitcnt=(.+?)\)',self.config)
        if '(inactive)' in self.config:
            self.InActive = True
        self.HexIdent = self.config.split()[-1]
        
        
        self.Name = self.config.split()[1]
        self.LineNo = self.config.split()[3]
        self.Type = self.config.split()[4]
        
        if self.Type == 'standard':
            self.Action = self.config.split()[5]
            self.Protocol = 'ip'
            Index = 6
            if self.config.split()[Index] == 'host':
                Index+=1
                self.SrcNet = IPNetwork(self.config.split()[Index]+'/32')
                Index+=1
            elif self.config.split()[Index] == 'object':
                Index+=1
                if INTENSIVE:
                    objName =   self.config.split()[Index]
                    ConfigHandler = CiscoConfigFW(self.DeviceName,objName)
                    self.SrcNet = ConfigHandler.Network_Objects()
                else:
                    self.SrcNet = self.config.split()[Index]
                Index+=1
            elif self.config.split()[Index] == 'object-group':
                Index+=1
                if INTENSIVE:
                    objName =   self.config.split()[Index]
                    ConfigHandler = CiscoConfigFW(self.DeviceName,objName)
                    self.SrcNet = ConfigHandler.NetworkObjectGroup()
                else:
                    self.SrcNet = self.config.split()[Index]
                Index+=1
            elif re.match(IP_REX,self.config.split()[Index]) :
                
                self.SrcNet = IPNetwork(self.config.split()[Index]+'/'+self.config.split()[Index+1])
                Index+=2
            elif self.config.split()[Index] ==  'any':
                self.SrcNet = IPNetwork('0.0.0.0/0')
                Index+=1
            
            self.SrcPort=CiscoPort('gt','0',self.Protocol)
            self.DstPort=CiscoPort('gt','0',self.Protocol)
            self.DstNet=IPNetwork('0.0.0.0/0')
            
        elif self.Type == 'extended':
            self.Action = self.config.split()[5]
            self.Protocol = self.config.split()[6]
            ####################
            #check for protocol objectgroup
            if self.Protocol == 'object-group' or self.Protocol == 'object':
                self.Protocol = self.config.split()[7]
                try:
                    self.Protocol = Service_Object_Dict[self.Protocol]
                except:
                    try:
                        self.Protocol = Service_Object_Group_Dict[self.Protocol]
                    except:
                        self.Protocol = Protocol_Object_Group_Dict[self.Protocol]
                        
                    
                Index +=1
                
                
            
            ####################
            #CHECK SRC NET
            if self.config.split()[Index] == 'host':
                Index+=1
                if Check_Valid_Netwok(self.config.split()[Index]):
                    self.SrcNet = IPNetwork(self.config.split()[Index]+'/32')
                else:
                    net = Network_Name_IP_Dict[self.config.split()[Index]].IP
                    self.SrcNet = IPNetwork(net+'/32')
                Index+=1
            elif self.config.split()[Index] == 'object':
                Index+=1
                if INTENSIVE:
                    objName =   self.config.split()[Index]
                    ConfigHandler = CiscoConfigFW(self.DeviceName,objName)
                    self.SrcNet = ConfigHandler.Network_Objects()
                else:
                    self.SrcNet = self.config.split()[Index]
                Index+=1
            elif self.config.split()[Index] == 'object-group':
                Index+=1
                if INTENSIVE:
                    objName =   self.config.split()[Index]
                    ConfigHandler = CiscoConfigFW(self.DeviceName,objName)
                    self.SrcNet = ConfigHandler.NetworkObjectGroup()
                else:
                    self.SrcNet = self.config.split()[Index]
                Index+=1
            elif re.match(IP_REX,self.config.split()[Index]) :
                
                self.SrcNet = IPNetwork(self.config.split()[Index]+'/'+self.config.split()[Index+1])
                Index+=2
            elif self.config.split()[Index] ==  'any' or self.config.split()[Index] ==  'any4':
                self.SrcNet = IPNetwork('0.0.0.0/0')
                Index+=1
            else:
                net = Network_Name_IP_Dict[self.config.split()[Index]].IP
                self.SrcNet = IPNetwork(net+'/'+self.config.split()[Index+1])
                Index+=2                
                
            #    
            ######################
            #print Index
            if self.Protocol == 'tcp' or self.Protocol == 'udp' or type(self.Protocol).__name__ == 'ProtocolObjectGroup':
                ######################
                #CHECK FOR SRC PORT
                if 'eq' == self.config.split()[Index]:
                    Index+=1
                    port = self.config.split()[Index]
                    if not re.match('\d+',port):
                        port = Get_Port_Number(port)
                    self.SrcPort=CiscoPort('eq',port,self.Protocol)
                    Index+=1
                    
                elif 'lt' == self.config.split()[Index]:
                    Index+=1
                    port = self.config.split()[Index]
                    if not re.match('\d+',port):
                        port = Get_Port_Number(port)
                    self.SrcPort=CiscoPort('lt',port,self.Protocol)
                    Index+=1
                    
                elif 'gt' == self.config.split()[Index]:
                    Index+=1
                    port = self.config.split()[Index]
                    if not re.match('\d+',port):
                        port = Get_Port_Number(port)
                    self.SrcPort=CiscoPort('gt',port,self.Protocol)
                    Index+=1
                    
                elif 'range' == self.config.split()[Index]:
                    Index+=1
                    port1 = self.config.split()[Index]
                    if not re.match('\d+',port1):
                        port1 = Get_Port_Number(port1)
                    Index+=1
                    port2 = self.config.split()[Index]
                    if not re.match('\d+',port2):
                        port2 = Get_Port_Number(port2)
                    self.SrcPort =CiscoPort('range',port1+'-'+port2,self.Protocol)           
                    Index+=1
                    
                elif 'object-group' == self.config.split()[Index]:
                    Index+=1
                    
                    if INTENSIVE:
                        objName =   self.config.split()[Index]
                        
                        ConfigHandler = CiscoConfigFW(self.DeviceName,objName)
                        self.SrcPort = ConfigHandler.ServiceObjectGroup()
                    else:
                        self.SrcPort = self.config.split()[Index]
                    Index+=1
                    #check if its port object or dst object
                    try:
                        Service_Object_Group_Dict[self.SrcPort]
                    except:
                        self.SrcPort=CiscoPort('gt','0',self.Protocol)
                        Index-=2
                    
                else:
                    #print 'all ports'
                    self.SrcPort=CiscoPort('gt','0',self.Protocol)
                #
                #####################
            #print 'dst',Index
            #####################
            #CHECK DST NET
            if self.config.split()[Index] == 'host':
                Index+=1
                if Check_Valid_Netwok(self.config.split()[Index]):
                    self.DstNet = IPNetwork(self.config.split()[Index]+'/32')
                else:
                    net = Network_Name_IP_Dict[self.config.split()[Index]].IP
                    self.DstNet = IPNetwork(net+'/32')
                Index+=1
            elif self.config.split()[Index] == 'object':
                Index+=1
                if INTENSIVE:
                    objName =   self.config.split()[Index]
                    ConfigHandler = CiscoConfigFW(self.DeviceName,objName)
                    self.DstNet = ConfigHandler.Network_Objects()
                else:
                    self.DstNet = self.config.split()[Index]
                Index+=1
            elif self.config.split()[Index] == 'object-group':
                Index+=1
                if INTENSIVE:
                    objName =   self.config.split()[Index]
                    
                    ConfigHandler = CiscoConfigFW(self.DeviceName,objName)
                    self.DstNet = ConfigHandler.NetworkObjectGroup()
                else:
                    self.DstNet =  self.config.split()[Index]
                Index+=1
            elif re.match(IP_REX,self.config.split()[Index]) :
                self.DstNet = IPNetwork(self.config.split()[Index]+'/'+self.config.split()[Index+1])
                Index+=2
            elif self.config.split()[Index] ==  'any' or self.config.split()[Index] ==  'any4':
                self.DstNet = IPNetwork('0.0.0.0/0')
                Index+=1
            else:
                net = Network_Name_IP_Dict[self.config.split()[Index]].IP
                self.DstNet = IPNetwork(net+'/'+self.config.split()[Index+1])
                Index+=2                 
            #
            ##########################
            if Index == len(self.config.split()):
                return
            #print 'port',Index
            if self.Protocol == 'tcp' or self.Protocol == 'udp' or type(self.Protocol).__name__ == 'ProtocolObjectGroup':
                ######################
                #CHECK FOR DST PORT
                if 'eq' == self.config.split()[Index]:
                    Index+=1
                    port = self.config.split()[Index]
                    if not re.match('\d+',port):
                        port = Get_Port_Number(port)
                    self.DstPort=CiscoPort('eq',port,self.Protocol)
                    Index+=1
                    
                elif 'lt' == self.config.split()[Index]:
                    Index+=1
                    port = self.config.split()[Index]
                    if not re.match('\d+',port):
                        port = Get_Port_Number(port)
                    self.DstPort=CiscoPort('lt',port,self.Protocol)
                    Index+=1
                    
                elif 'gt' == self.config.split()[Index]:
                    Index+=1
                    port = self.config.split()[Index]
                    if not re.match('\d+',port):
                        port = Get_Port_Number(port)
                    self.DstPort=CiscoPort('gt',port,self.Protocol)
                    Index+=1
                    
                elif 'range' == self.config.split()[Index]:
                    Index+=1
                    port1 = self.config.split()[Index]
                    if not re.match('\d+',port1):
                        port1 = Get_Port_Number(port1)
                    Index+=1
                    port2 = self.config.split()[Index]
                    if not re.match('\d+',port2):
                        port2 = Get_Port_Number(port2)
                    self.DstPort =CiscoPort('range',port1+'-'+port2,self.Protocol)           
                    Index+=1
                elif 'object-group' == self.config.split()[Index]:
                    Index+=1
                    if INTENSIVE:
                        objName =   self.config.split()[Index]
                        Index+=1
                        ConfigHandler = CiscoConfigFW(self.DeviceName,objName)
                        self.DstPort = ConfigHandler.ServiceObjectGroup()
                    else:
                        self.DstPort =self.config.split()[Index]

                else:
                    self.DstPort=CiscoPort('gt','0',self.Protocol)
                #
                #####################
                #if type(self.DstPort).__name__ == 'CiscoPort' and type(self.SrcPort).__name__ == 'CiscoPort' :
                #self.ServiceGroup = TCPUDP(self.Protocol,self.SrcPort,self.DstPort)
                '''
            elif self.Protocol == 'ip':
                self.ServiceGroup = IP()
                '''    
            elif self.Protocol == 'icmp':
                #
                #
                #TO DO : ADD ICMP OBJECT LIST
                #
                if 'object-group' in self.config.split()[Index]:
                    Index+=1
                    self.DstICMPType = self.config.split()[Index]
                    self.DstICMPType = ICMP_TYPE_Object_Group_Dict[self.DstICMPType]
                    #self.ServiceGroup = self.config.split()[Index]
                    
                    
                    
                elif '(hitcnt' not in self.config.split()[Index] and 'time-range' not in self.config.split()[Index] and '0x' not in self.config.split()[Index] and 'inactive' not in self.config.split()[Index] and 'log' not in self.config.split()[Index] :
                    self.DstICMPType = self.config.split()[Index]
                    if not re.match('\d+',self.DstICMPType):
                        self.DstICMPType=Get_ICMP_Type(self.DstICMPType)
                    
                    Index+=1
                else:
                    self.DstICMPType = None
                    #self.ServiceGroup = ICMP()
                    #self.DstICMPType = '0-255'

                
            """
                
            """

            
            #print Index   
            if 'time-range' in self.config.split():
                i = self.config.split().index('time-range')
                self.TimeRange = self.config.split()[i+1]
            #print self.SrcNet
            #print self.DstNet
            #print self.DstPort
            
        
                        
                                        
INTENSIVE = False        

