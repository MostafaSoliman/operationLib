class IP(object):
    """
        CLASS FOR IP OBJECT PROTOCOL 
        
    """
    def __init__(self,Protocol=None):
        if Protocol:
            self.Protocol = Protocol
        else:
            self.Protocol = 'ip'
        self.Name =   'IP '+str(self.Protocol)
        
class ICMP(IP):
    """
        CLASS FOR ICMP OBJECT PROTOCOL ICMPTYPE
        
    """
    def __init__(self,ICMPType=None,ICMPCode=None):
        self.Protocol = 'icmp'
        if ICMPType:
            self.ICMPType = int(ICMPType)
        self.ICMPType = ICMPType
        self.ICMPCode = ICMPCode
        self.Name =   'ICMP '+str(self.ICMPType )   

class IPSEC(object):
    """
    IPSEC object
    """
class NOS(object):
    """
    """
class PPTP(object):
    """
    """

class CiscoPort(object):
    """
        CLASS TO PERFORM OPERATION ON PORTS OBJECTS
        """
    def __init__(self,operator,port,Protocol):
        self.operator = operator
        self.Protocol = Protocol
        self.port = port
        if '-' not in self.port:
            self.Name =  self.operator +' '+self.port
        else:
            self.Name =  self.operator +' '+self.port.split('-')[0]+' '+self.port.split('-')[1]
    def Check_Port(self,port):
        """
        CHECK IF GIVEN PORT IS INCLUDED IN THE PORT OBJECT
    """
        port = int(port)
        if self.operator == 'eq':
            if port == int(self.port):
                return True
            else:
                return False
        if self.operator == 'lt':
            if port < int(self.port):
                return True
            else:
                return False
        if self.operator == 'gt':
            if port > int(self.port):
                return True
            else:
                return False
        if self.operator == 'range':
            port1,port2 = self.port.split('-')
            if port >= int(port1) and port <= int(port2) :
                return True
            else:
                return False 




class TCPUDP(object):
    """
        OBJECT REPRESEND SRC PORT DEST PORT AND PROTOCOL
    """
    def __init__(self,Protocol,SrcPort,DstPort):
        self.Protocol = Protocol
        self.SrcPort = SrcPort
        self.DstPort = DstPort
        self.Name = Protocol+' '+SrcPort.Name+' '+DstPort.Name
    

'''
p = Port('range','10-65555')
print p.Check_Port('200')
'''
