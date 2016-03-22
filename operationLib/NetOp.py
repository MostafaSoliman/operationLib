from netaddr import IPNetwork,IPAddress
import re
IP_REX = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'


def Check_Subnets_Errors(output):
    if '255.255.252.255' in output:
        print 'found'
        output = output.replace('255.255.252.255','255.255.255.255')
    return output
def Check_Valid_Netwok(net):
    if re.match(IP_REX,net):
        return True
    return False
def Get_IP_Protocol_No(IP):
    try:
        return {
                'ah':'51',
                'eigrp':'88',
                'esp':'50',
                'gre':'47',
                'igmp':'2',
                'igrp':'9',
                'ipinip':'4',
                'ospf':'89',
                'pcp':'108',
                'pim':'103',
                'snp':'109'

          }[IP]
    except KeyError:
        print 'WARRNING::KeyError Catched,IP PROTOCOL NOT IN list.',IP
        return None    

def Get_ICMP_Type(ICMPName):
    try:
        return {
            'alternate-address':'6',
            'conversion-error':'31',
            'information-reply':'16',
            'information-request':'15',
            'mask-reply':'18',
            'mask-request':'17',
            'mobile-redirect':'32',
            'parameter-problem':'12',
            'redirect':'5',
            'router-advertisement':'9',
            'router-solicitation':'10',
            'source-quench':'4',
            'timestamp-reply':'14',
            'timestamp-request':'13',
            'echo-reply':'0',
            'unreachable':'3',
            'echo':'8',
            'time-exceeded':'11',
            'traceroute':'30'

          }[ICMPName]
    except KeyError:
        print 'WARRNING::KeyError Catched,ICMP TYPE NOT IN list.',ICMPName
        return None
    
def Get_Port_Number(PortsName):
    #print 'convert port',PortsName
    try:
        return {
                'radius-acct':'1646',
                'rsh':'514',
                'rdp':'3389',
                'sftp':'22',
                'nfs':'2047',
                'aol':'5190',
                'bgp':'179',
                'biff':'512',
                'bootpc':'68',
                'bootps':'67',
                'chargen':'19',
                'citrix-ica':'1494',
                'cmd':'514',
                'ctiqbe':'2748',
                'daytime':'13',
                'discard':'9',
                'domain':'53',
                'dnsix':'195',
                'echo':'7',
                'exec':'512',
                'finger':'79',
                'ftp':'21',
                'ftp-data':'20',
                'gopher':'70',
                'https':'443',
                'http':'80',
                'h323':'1720',
                'hostname':'101',
                'ident':'113',
                'imap4':'143',
                'irc':'194',
                'isakmp':'500',
                'kerberos':'750',
                'klogin':'543',
                'kshell':'544',
                'ldap':'389',
                'ldaps':'636',
                'lpd':'515',
                'login':'513',
                'lotusnotes':'1352',
                'mobile-ip':'434',
                'nameserver':'42',
                'netbios-ns':'137',
                'netbios-dgm':'138',
                'netbios-ssn':'139',
                'nntp':'119',
                'ntp':'123',
                'pcanywhere-status':'5632',
                'pcanywhere-data':'5631',
                'pim-auto-rp':'496',
                'pop2':'109',
                'pop3':'110',
                'pptp':'1723',
                'radius':'1645',
                'rip':'520',
                'secureid':'5510',
                'smtp':'25',
                'snmp':'161',
                'snmptrap':'162',
                'sqlnet':'1521',
                'ssh':'22',
                'sunrpc':'111',
                'syslog':'514',
                'tacacs':'49',
                'talk':'517',
                'telnet':'23',
                'tftp':'69',
                'time':'37',
                'uucp':'540',
                'who':'513',
                'whois':'43',
                'sip':'5060',
                'www':'80',
                'xdmcp':'177',
                'rtsp':'554'

            
          
        }[PortsName]
    except KeyError:
        print 'WARRNING::KeyError Catched, port name not in list.',PortsName
        return None

def Check_Network_in_Network(Net1,Net2):
    if IPNetwork(Net1) in IPNetwork(Net2):
        return True

    else:
        return False

########################################################################################################################################################
#check for largest prfx
#if many found ,lowest AD
#if many found ,Lowest metric

def Best_Route(NetmaskList,ADList,MetricList):
    #print NetmaskList,ADList,MetricList
    MaxNetmaskIndex=0
    MaxNetmaskIndexList=[]
    ADIndexList=[]
    MinMetricIndexList=[]
    
    for i in range (len(NetmaskList)):
        if IPAddress(NetmaskList[i])>IPAddress(NetmaskList[MaxNetmaskIndex]):
            MaxNetmaskIndex=i
    if NetmaskList.count(NetmaskList[MaxNetmaskIndex])>1:
        #print 'found many with same max prefx'
        for i in range (len(NetmaskList)):
            if NetmaskList[i]==NetmaskList[MaxNetmaskIndex]:
                MaxNetmaskIndexList.append(i)
        MinADIndex=0
        for i in MaxNetmaskIndexList: #find min ad in max prefx
            if (ADList[i])<(ADList[MinADIndex]):
                MinADIndex=i
        if Count_Min_List(ADList,ADList[MinADIndex],MaxNetmaskIndexList)>1:
            #print 'found many with same max prefx+min AD'
            for i in MaxNetmaskIndexList: 
                if (ADList[i])==(ADList[MinADIndex]):
                    ADIndexList.append(i)
            MinMetricIndex=0
            for i in ADIndexList: 
                if (MetricList[i])<(MetricList[MinMetricIndex]):
                    MinMetricIndex=i
            print 'min metric',MetricList[MinMetricIndex]
            if Count_Min_List(MetricList,MetricList[MinMetricIndex],ADIndexList)>1:
                print 'found many with same max prefx+min AD + min metric'
                print 'note data will load balnced between them'
                
                for i in ADIndexList:
                    if MetricList[i]==MetricList[MinMetricIndex]:
                        MinMetricIndexList.append(i)
                return MinMetricIndexList
            else:
                return MinMetricIndex
        else:
            return MinADIndex
    else:
        return MaxNetmaskIndex
######################################################################################################################
