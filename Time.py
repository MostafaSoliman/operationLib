import datetime


class TimeDate(object):
    def __init__(self,hour,minute,day,month,year,second=0):
        #
        #ALL INPUT ARGS ARE TYPE INT
        #
        self.time = datetime.time(hour,minute,second)
        self.date = datetime.date(year,month,day)

    def __eq__(self,TDObj):
        if isinstance(TDObj,TimeDate):
            if self.time == TDObj.time and self.date == TDObj.date :
                return True
            else:
                return False
        else:
            return NotImplemented

    def __lt__(self,TDObj):
        #OLDER
        
        if isinstance(TDObj,TimeDate):
            if self.date < TDObj.date :
                return True
            elif self.date == TDObj.date:
                if self.time < TDObj.time:
                    return True
                else:
                    return False

        else:
            return NotImplemented        
        
    def __gt__(self,TDObj):
        #NEWER
        
        if isinstance(TDObj,TimeDate):
            if self.date > TDObj.date :
                return True
            elif self.date == TDObj.date:
                if self.time > TDObj.time:
                    return True
                else:
                    return False

        else:
            return NotImplemented         
        
        
