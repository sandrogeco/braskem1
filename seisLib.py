import matplotlib.pyplot as plt
plt.switch_backend('agg')
import os
import logging
from obspy import UTCDateTime
from obspy.core.stream import Stream
from obspy.clients.filesystem.sds import Client

import multiprocessing
import obspy.signal.polarization
from obspy import read_inventory
import obspy.signal


import json
import psycopg2
import time
import numpy as np

from sch import log
import urllib.request, json

dpi = 100
sizex = 800
sizey = 600
yRange = 0.1

hystType = [360, 180, 60]

band = {
    'low': [1, 20],
    'high': [20, 50]
}

rTWindow = 360
rtSft = 2


class sysStations():
    _refresh=5
    _network=''

    def __init__(self,sts,net,table='seismic.stations',refresh=5):
        self._stations=multiprocessing.Manager().dict()
        self._alarms=multiprocessing.Manager().dict()

        self._raw=multiprocessing.Manager().list()
        self._refresh=refresh
        self._network=net
        for s in sts:
            self._stations[net+"_"+s]=sysStation(s,net)
        self._table = table



    def updateStz(self,*args):#key,attr,value):
        if len(args)==1:
            a=args[0]
            key=[a._intName]
        if len(args)==3:
            key=[args[0]]
            if key=='*':
                key=[s._intName for s in self._stations]
            attr=args[1]
            value=args[2]
        for k in key:
            latencyOld=self._stations[k]
            statusOld=self._stations[k]
            a=self._stations[k]
            a.__setattr__(attr,value)
            self.statusCalc(a,k)
            if (a._latency!=latencyOld) or (a._status!=statusOld):
                self.updateDB(a)


    def run(self,table='seismic.alarms'):

        while 1<2:

            time.sleep(self._refresh)
            try:
                self.connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
                                                   password='Bebedouro77627')
            except:
                print('DB connection failed')
                pass

            t=UTCDateTime.now()
            a=self._alarms.copy()
            try:
                [self._alarms.pop(e) for e in a.keys() if (a[e]._time + a[e]._tOff < UTCDateTime.now())]
            except:
                pass
            print('XXXX'+UTCDateTime.now().strftime("'%Y-%m-%d %H:%M:%S'"))

            for s in self._stations.keys():
                a=self._stations[s]
                al=[e for e in self._alarms.values() if e._station==s]
                sql="delete from "+table+" where station='"+s+"';"
                try:
                    self.connection.cursor().execute(sql)
                    self.connection.commit()
                except:
                    print('DB update failed')
                    pass
                l = 1
                if len(al)>0:
                    for e in al:
                        if e._level>l:
                            l=e._level
                        sql = "insert into "+table+" (station,time,level,text_to_disp,event_type) VALUES ('" \
                              + s + "',"+e._time.strftime("'%Y-%m-%d %H:%M:%S'")\
                              +","+str(e._level)+",'"+e._text+"',"+e._type+");"
                        try:
                            self.connection.cursor().execute(sql)
                            self.connection.commit()
                        except:
                            print('DB update failed')
                            pass

                        print(e._station+' '+e._type+' '+e._text+' '+e._time.strftime("'%Y-%m-%d %H:%M:%S'")+ ' '+str(e._tOff))
                        print(self._stations[s]._latency)

                if a._latency > a._maxLatency:
                    a._status = 0
                else:
                    a._status = l
                # self.updateDB(a)
                sql = "update " + self._table + " set latency=" + str(a._latency) + ", status=" + str(
                    a._status) + " where name='" + str(
                    a._intName) + "';"
                try:
                    self.connection.cursor().execute(sql)
                    self.connection.commit()
                except:
                    print('station DB update failed')
                pass
            self.connection.close()

    def insertAlert(self,time,k,type,l,tOff,text=''):
        if k=="'*'" or k=='*' or k=="*":
            k=[n for n in  self._stations.keys()]
        # else:
        #     k=[k]

        for kk in k:
            e=eventAlert(UTCDateTime(time),type,kk,l,np.int(tOff),text)
            #self._alarms.append(e)
            self._alarms[kk+type+UTCDateTime(time).strftime("'%Y-%m-%d %H:%M:00'")]=e


    def updateLatency(self,key,l):
        # if key == "'*'":
        #     key = [s._intName for s in self._stations]
        #for k in key:
            #self._stations[k].__setattr__('_latency',l)
        a=self._stations[key]
        a._latency=l
        self._stations[key]=a
            # self.statusCalc(a,k)

    def statusCalc(self,a,key):
        l=1
        if a._latency > a._maxLatency:
            a._status = 0
        else:
            l=np.max([a._CL_HR,a._HR,a._AM,a._MAG])
            a._status = l

        self._stations[key] = a

    def updateDB(self,station):
        sql = "update " + self._table + " set latency=" + str(station._latency) + ", status=" + str(
            station._status) + " where name='" + str(
            station._intName) + "';"
        try:
            self.connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
                                               password='Bebedouro77627')
            self.connection.cursor().execute(sql)
            self.connection.commit()
            self.connection.close()
        except:
            print('station DB update failed')
            pass

class eventAlert():
    _type=''
    _text=''
    _level=0
    _tOff=2/60
    _station=''
    _time=UTCDateTime

    def __init__(self,time=UTCDateTime.now(),type='',station='',level=0,tOff=2/60,text=''):
        self._type = type
        self._text = text
        self._level = level
        self._tOff = tOff
        self._station=station
        self._time=time

class sysStation():


    _CL_HR=0
    _HR=0
    _AM=0
    _MAG=0
    _alList=[]#eventAlert
    _status=1
    _latency=0
    _name=''
    _network=''
    _intName=''
    _maxLatency=60*60


    def __init__(self,name,net):
        self._name=name
        self._network=net
        self._intName=self._network+"_"+self._name

class alert():
    _sysStations=sysStations
    _confFile='pp.json'
    _time=UTCDateTime
    _a={
        'id_alert':"''",
        'utc_time':'',
        'utc_time_str':'',
        'event_type':"''",
        'station':"''",
        'channel':"''",
        'amplitude_ehe':0,
        'amplitude_ehn':0,
        'amplitude_ehz':0,
        'linearity':0,
        'az':0,
        'az_err':0,
        'tkoff_err':0,
        'tkoff':0,
        'freq':0,
        'lat':0,
        'lon':0,
        'note':"''",
        'rate':0,
        'level':0,
        'magnitudo':0,
        'id_casp':0,
        'depth':0,
        'rel':False,
        'erh':0,
        'erz':0,
        'max_amplitude':0,
        'median_amplitude':0,
        'mean_amplitude':0
    }
    _log = {
        'lastElab': UTCDateTime.now()
    }
    _aList=[]
    _table=''
    _isAC=False

    _th={#soglie su cui definire rate
        'AML':0.00005,
        'AMH':0.00005,
        'CASP':0
    }
    _rTh = {#soglie rate
        'AML': 0,
        'AMH': 0,
        'CASP':0,
        'wnd':1,
        'sft':0.25
    }
    _rateX=[]
    _amplY=[]
    _thMatrix=[]
    _clusters=[]
    _clTh={
        'lag':3600
    }

    def __init__(self,table='seismic.alerts'):
        self.connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
                                      password='Bebedouro77627')
        self._table=table

    def __del__(self):
        self.connection.close()


    def insert(self,s0=True,clause=''):
        try:
            t=self._time
            if s0:
                self._a['utc_time']=t.strftime("'%Y-%m-%d %H:%M:00'")
                self._a['utc_time_str']=t.strftime("'%Y-%m-%d %H:%M:00'")
            else:
                self._a['utc_time'] = "'"+t.strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]+"'"
                self._a['utc_time_str'] = "'"+t.strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]+"'"
            sql = "INSERT INTO " + self._table + " ("+"".join(str(s) + "," for s in self._a.keys())
            sql = sql[0:-1]
            sql += ") SELECT "+"".join( str(s) + "," for s in self._a.values())
            sql = sql[0:-1]
            sql += " WHERE NOT EXISTS( SELECT * FROM " + self._table + " WHERE utc_time=" + self._a['utc_time'] + \
                   " AND  station=" + self._a['station'] + " AND event_type=" + self._a['event_type'] + ");"
            cur=self.connection.cursor()
            cur.execute(sql)
            self.connection.commit()

        except:
            pass


    def getAlerts(self,ts,te,station='', event_type='',extra=''):
        r = False
        try:
            sql="SELECT "+"".join(str(s) + "," for s in self._a.keys())
            sql = sql[0:-1]

            if te==ts:
                sql += " FROM " + self._table + " WHERE station='" + station + "' AND event_type='" + event_type + \
                       "' AND utc_time='" + UTCDateTime(ts).strftime("%Y-%m-%d %H:%M:%S") + "' " + extra + " ;"
            else:
                sql+=" FROM "+self._table+ " WHERE station='"+station+"' AND event_type='"+event_type+\
                    "' AND utc_time>'"+UTCDateTime(ts).strftime("%Y-%m-%d %H:%M:%S")+\
                "' AND utc_time<='"+UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S")+"' "+extra+" ;"
            cr = self.connection.cursor()

            cr.execute(sql)
            p = cr.fetchall()
            #self.connection.commit()
            self._aList=[]

            for pp in p:
                r=True
                i=0
                at = {}
                for c in self._a.keys():
                    at[c]=pp[i]
                    i+=1
                self._aList.append(at)

        except:
            print('getting dets failed')
            pass

        return r

    def hourlyRateMag(self,te,station,type='CASP'):
        print('HR_CASP'+str(te))
        r=False
        ts=te-3600*self._rTh['wnd']
        self.getAlerts(ts,te,station,type)
        aa=[]
        for a in self._aList:
            if a['magnitudo']>self._th[type]:
                aa.append(a)


        self._time=te
        self._a['station'] = "'*'"
        self._a['event_type'] = "'HR_"+type+"'"
        self._a['rate'] = len(aa)/self._rTh['wnd']
        try:
            ampl = np.max([a['magnitudo'] for a in aa])
        except:
            ampl=0
        self._a['magnitudo']=ampl
        fR = np.where(self._rateX >= self._a['rate'])[0]
        fA = np.where(self._amplY <= ampl)[0]
        fR = fR[0]
        fA = fA[0]
        self._a['level'] = np.int(self._thMatrix[fA, fR])

        self.insert()
        if self._a['level']>0:
            self._sysStations.insertAlert(te, "'*'", self._a['event_type'], self._a['level']+1, 2*self._rTh['sft'] * 3600,
                                          'CASP hourly rate alarm ')

        r=True
        return r


    def hourlyRate(self,te,station,type='AML'):
        r=False
        ts=te-3600*self._rTh['wnd']
        self.getAlerts(ts,te,station,type)
        aa=[]
        for a in self._aList:
            if (a['amplitude_ehe']>self._th[type]) or (a['amplitude_ehn'] > self._th[type]) or (a['amplitude_ehz'] > self._th[type]):
                aa.append(a)
        if len(aa)>self._rTh[type]:
            self._time=te
            self._a['event_type'] = "'HR_"+type+"'"
            self._a['station'] = "'"+station+"'"
            self._a['amplitude_ehe'] =np.median([m['amplitude_ehe'] for m in aa])
            self._a['amplitude_ehn'] =np.median([m['amplitude_ehn'] for m in aa])
            self._a['amplitude_ehz'] =np.median([m['amplitude_ehz'] for m in aa])
            self._a['rate'] = len(aa)/self._rTh['wnd']
            ampl = np.max([self._a['amplitude_ehz'], self._a['amplitude_ehe'], self._a['amplitude_ehn']])
            fR = np.where(self._rateX >= self._a['rate'])[0]
            fA = np.where(self._amplY <= ampl)[0]
            fR = fR[0]
            fA = fA[0]
            self._a['level'] = np.int(self._thMatrix[fA, fR])
            print(type+' '+station+' '+str(self._a['rate'])+' '+str(self._a['level']))
            self.insert()
            r=True
        return r

    def hourlyRateAmplitude(self,te,station,type='AML'):
        r=False
        ts=te-3600*self._rTh['wnd']
        self.getAlerts(ts,te,station,type)
        aa=self._aList
        if len(aa)>0:
            self._time=te
            self._a['event_type'] = "'HR_"+type+"'"
            self._a['station'] = "'"+station+"'"
            self._a['max_amplitude'] =np.max([m['max_amplitude'] for m in aa])
            self._a['median_amplitude'] =np.median([m['median_amplitude'] for m in aa])
            self._a['mean_amplitude'] = np.mean([m['mean_amplitude'] for m in aa])
            self._a['rate'] = np.sum([m['rate'] for m in aa])
            # fR = np.where(self._rateX >= self._a['rate'])[0]
            # fA = np.where(self._amplY <= self._a['max_amplitude'])[0]
            # fR = fR[0]
            # fA = fA[0]
            # self._a['level'] = np.int(self._thMatrix[fA, fR])
            print(type+' '+station+' '+str(self._a['rate'])+' '+str(self._a['max_amplitude']))
            self.insert()
            r=True
        return r





    def HR_run(self,st,aType):

        l=log()
        te=l.rdLog()

        while 1<2:
            if te<UTCDateTime.now():

                if 'AML' in aType:
                    print('AML ' + te.strftime("%Y-%m-%d %H:%M:%S"))
                    for s in st:
                        self.hourlyRate(te, s, 'AML')
                if 'AMH' in aType:
                    print('AMH ' + te.strftime("%Y-%m-%d %H:%M:%S"))
                    for s in st:
                        self.hourlyRate(te, s, 'AMH')
                if 'CASP' in aType:
                    print('CASP ' + te.strftime("%Y-%m-%d %H:%M:%S"))
                    self.hourlyRateMag(te,'*','CASP')
                if 'CL' in aType:
                    print('CL ' + te.strftime("%Y-%m-%d %H:%M:%S"))
                    self.clusterStation(te, self._clusters, self._clTh['lag'], 'HR_AML')
                l.wrLog(te)
                te=te+self._rTh['sft']*3600

            else:
                time.sleep(10)


    def clusterStation(self,te,cl,lag=3600,evType='HR_AML'):
        for stGroup in cl:
            print('CLUSTER AN')
            ll=[]
            n = 0
            try:
                for st in stGroup:
                    if self.getAlerts(te - np.int(lag), te, st, evType): # 'ORDER BY utc_time DESC LIMIT 1'):
                        l=np.max([a['level'] for a in self._aList])
                        if l>0:
                            ll.append(l)
                            n += 1
            except:
                pass
            l=0
            if len(ll) == len(stGroup):
                l=np.max(ll)
                for st in stGroup:
                    self._time=te
                    self._a['event_type'] = "'CL_" + evType + "'"
                    self._a['station'] = "'" + st + "'"
                    self._a['level'] = l
                    self.insert()
            #self._sysStations.updateStz(st,'_CL_HR',l)
            if l>0:
                self._sysStations.insertAlert(te,[st],self._a['event_type'],l+1,2*self._rTh['sft']*3600,'Cluster hourly rate alarm ')

    def clusterAn(self,te,cl,evType='HR_AML'):

        ll=[]
        n = 0
        try:
            print('CLUSTER AN ' + str(te))
            for st in cl:
                if self.getAlerts(te, te, st, evType): # 'ORDER BY utc_time DESC LIMIT 1'):
                    for a in self._aList:
                        fR = np.where(self._rateX >= a['rate'])[0]
                        fA = np.where(self._amplY <= a['mean_amplitude'])[0]
                        fR = fR[0]
                        fA = fA[0]
                        l= np.int(self._thMatrix[fA, fR])

                    if l>0:
                        ll.append(l)
                        n += 1
                print('     st:'+st+'    level='+str(l)+ '    ampl='+str(a['mean_amplitude'])+'   rate='+str(a['rate']))
        except:
            pass
        l=0
        if len(ll) == len(cl):
            l=np.max(ll)
            for st in cl:
                self._time=te
                self._a['event_type'] = "'CL_" + evType + "'"
                self._a['station'] = "'" + st + "'"
                self._a['level'] = l
                self.insert()
        #self._sysStations.updateStzggggggggggggggggg(st,'_CL_HR',l)
        if l>0:
            self._sysStations.insertAlert(te,[st],self._a['event_type'],l+1,2*self._rTh['sft']*3600,'Cluster hourly rate alarm ')

class drumPlot(Client):

    _log={
        'lastRcv':  UTCDateTime.now(),
        'lastCASP': UTCDateTime.now(),
        'lastDrum': UTCDateTime.now(),
    }

    _rTh = {
        'AML': 0,
        'AMH': 0,
        'CASP':0,
        'wnd':1,
        'sft':0.25
    }
    _rsp=250
    _lastElaborate=UTCDateTime
    _sysStations = sysStations
    _traces = Stream()
    _inv = read_inventory("metadata/Braskem_metadata.xml")
    _rtSft = rtSft
    _lastData = UTCDateTime.now()
    _traces = Stream()
    _2minRTraces=Stream()
    _appTrace = Stream()
    _drTrace = Stream()
    _drHTrace = Stream()
    _rTWindow = rTWindow
    _tEnd = UTCDateTime.now()
    _tNow = UTCDateTime.now()
    _rtRunning = False
    _hyRunning = False
    _saving = False
    _elRunning = False
    _status = {}
    _elab = {}
    _elabHyst={}
    _events = []
    _alertTable=''
    _localTimeOffset=0
    _amplAn = {
        'lowFW': [1,20],
        'highFW': [20,50],
        'lowFTh': 0.00001,
        'highFTh': 0.00005,
        'sft':1/3600,
        'wnd':1/3600
    }



    def rtCASP(self,acq=True):

        l=log()

        te=l.rdLog()
        while 1<2:
            if te<UTCDateTime.now():
                print('CASP ' + te.strftime("%Y-%m-%d %H:%M:%S"))
                try:
                    if acq:
                        self.getCasp()

                    self.rtAlertCASP(te)
                    l.wrLog(self._tEnd)
                except:
                    print('CASP events forwarding failed')
                    pass
                te=te+self._rTh['sft']*3600
            else:
                time.sleep(10)


    def plotDrum(self, trace, filename='tmp.png'):
        try:
            trace.data = trace.data * 1000 / 3.650539e+08
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            trace.interpolate(sampling_rate=trace.stats['sampling_rate'], time_shift=self._localTimeOffset)
            trace.plot(type='dayplot',
                            dpi=dpi,
                            x_labels_size=int(8 * 100 / int(dpi)),
                            y_labels_size=int(8 * 100 / int(dpi)),
                            title_size=int(1000 / int(dpi)),
                            title=(self._tEnd+self._localTimeOffset).strftime("%Y/%m/%d %H:%M:%S"),
                            size=(sizex, sizey),
                            color=('#AF0000', '#00AF00', '#0000AF'),
                            vertical_scaling_range=yRange,
                            outfile=filename,
                            show_y_UTC_label=True,
                            #handle=True,
                            time_offset=-3,
                            data_unit='mm/s',
                            events=self._events
                            )
            self._log['lastDrum'] = self._tEnd
            return True
        except:
            print('ops,something wrong in plotting!!')
            return False

    def plotDrum1(self, trace, filename='tmp.png'):
        try:
            trace.data = trace.data * 1000 / 3.650539e+08
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            trace.interpolate(sampling_rate=trace.stats['sampling_rate'], time_shift=self._localTimeOffset)
            trace.plot(type='dayplot',
                            dpi=dpi,
                            x_labels_size=int(8 * 100 / int(dpi)),
                            y_labels_size=int(8 * 100 / int(dpi)),
                            title_size=int(1000 / int(dpi)),
                            title=(trace.stats['starttime']).strftime("%Y/%m/%d %H:%M:%S")+' - '+(trace.stats['endtime']).strftime("%Y/%m/%d %H:%M:%S"),
                            size=(sizex, sizey),
                            color=('#AF0000', '#00AF00', '#0000AF'),
                            vertical_scaling_range=yRange,
                            outfile=filename,
                            show_y_UTC_label=False,
                            #handle=True,
                            time_offset=-3,
                            data_unit='mm/s',
                            events=self._events
                            )
            return True
        except:
            print('ops,something wrong in plotting 1!!')
            return False


    def realTimeDrumPlot(self):
        print('RealTime plot start ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        appTrace = Stream()
        self._rtRunning = True
        for tr in self._traces:
            id = tr.get_id()
            spl = id.split('.')
            network = spl[0]
            station = spl[1]
            channel = spl[3]
            l = int(self._tEnd - tr.stats['endtime'])
            if channel=='EHZ':
               # self._sysStations.updateStz(network+"_"+station,'_latency',l)
                self._sysStations.updateLatency(network+"_"+station,l)
            self._status[station] = {}
            self._status[station]["Noise Level"] = "---"
            self._status[station]["Latency"] = str(l) + 's'
            self._status[station]["Voltage"] = "---"
            self._status[station]["Color"] = "#FF0000"

            for b in band:
                fileNameRT = 'RT_' + network + '_' + station + '_' + channel + '_' + str(b) + '.png'
                appTrace = tr.copy()
                bb = band[b]
                appTrace.trim(self._tEnd - self._rTWindow * 60, self._tEnd, pad=True, fill_value=0)
                appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                self.plotDrum(appTrace, self._basePathRT + 'RT/' + fileNameRT)

 #       self._stations.updateStationLatency()



        print('realTime end ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        self._rtRunning = False

    def hystDrumPlot(self):
        tEnd=self._tEnd+self._localTimeOffset
        appTrace = Stream()
        self._hyRunning = True
        # if tEnd==0:
        #     tEnd=self._tEnd
        # else:
        #     self._tEnd=tEnd
        print('Hyststart ' + tEnd.strftime("%Y%m%d %H%M%S"))
        for tr in self._traces:
            id = tr.get_id()
            # print('hyst '+id)
            spl = id.split('.')
            network = spl[0]
            station = spl[1]
            channel = spl[3]

            for h in hystType:

                if tEnd.hour % int(h / 60) == 0:
                    for b in band:
                        tStart = tEnd - h * 60
                        p = network + '/' + station + '/' + channel + '/' + str(tStart.year) + '/' + str(
                            tStart.month) + '/' + str(
                            tStart.day) + '/' + str(h) + '/' + str(b)

                        fileName = p + '/' + tStart.strftime("%Y%m%d%H")+ '00.png'
                        appTrace = tr.copy()
                        bb = band[b]
                        appTrace.trim(tStart-self._localTimeOffset, tEnd-self._localTimeOffset, pad=True, fill_value=0)
                        appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                        self.plotDrum(appTrace, self._basePath + fileName)
        self._hyRunning = False

    def singleStationRealTimeDrumPlot(self,te,network,station):
        print('RealTime plot start ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))

        a=alert(self._alertTable)
        a.getAlerts(self._tEnd - 3600 * 24, self._tEnd, '*', 'CASP')
        self._events = [
            dict(time=UTCDateTime(aa['utc_time']) + self._localTimeOffset, text='CASP ev. mag' + str(aa['magnitudo']))
            for aa in a._aList]

        tEnd = te
        tStart=tEnd-60*self._rTWindow
        for b in self._band:
            traces = self.get_waveforms(network, station, '', 'EH?', tStart, tEnd)
            traces.merge()
            for tr in traces:
                id = tr.get_id()
                spl = id.split('.')
                channel = spl[3]
                fileNameRT = 'RT_' + network + '_' + station + '_' + channel + '_' + str(b) + '.png'
                appTrace = tr.copy()
                bb = self._band[b]
                appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                self.plotDrum1(appTrace, self._basePathRT + 'RT/' + fileNameRT)



    def singleStationHystDrumPlot(self,te,network,station):
        tTrg = te + self._localTimeOffset
        for h in self._hystType:
            if tTrg.hour % int(h / 60) == 0:
                print('Hyststart ' + te.strftime("%Y%m%d %H%M%S"))
                tStart = te - h * 60
                a = alert(self._alertTable)
                a.getAlerts(tStart, te, '*', 'CASP')
                self._events = [
                    dict(time=UTCDateTime(aa['utc_time']) + self._localTimeOffset,
                         text='CASP ev. mag' + str(aa['magnitudo']))
                    for aa in a._aList]
                traces = self.get_waveforms(network, station, '', 'EH?', tStart, te)
                traces.merge()
                for b in self._band:
                    for tr in traces :
                        id = tr.get_id()
                        spl = id.split('.')
                        channel = spl[3]
                        p = network + '/' + station + '/' + channel + '/' + str(tStart.year) + '/' + str(
                            tStart.month) + '/' + str(
                            tStart.day) + '/' + str(h) + '/' + str(b)

                        fileName = p + '/' + tStart.strftime("%Y%m%d%H") + '00.png'
                        appTrace = tr.copy()
                        bb = self._band[b]
                        appTrace.trim(tStart,te, pad=True,fill_value=0)
                        appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                        self.plotDrum1(appTrace, self._basePath + fileName)

    def An(self,table='seismic.alerts'):
        self._elRunning=True
        appTrace=self._2minRTraces.copy()
        ts=self._tEnd-70
        te=self._tEnd-10

        appTraceLow = self._2minRTraces.copy()
        appTraceLow.filter('bandpass', freqmin=self._amplAn['lowFW'][0], freqmax=self._amplAn['lowFW'][1], corners=3,
                        zerophase=True)
        appTraceLow.trim(ts,te)

        appTraceHigh = self._2minRTraces.copy()
        appTraceHigh.filter('bandpass', freqmin=self._amplAn['highFW'][0], freqmax=self._amplAn['highFW'][1], corners=3,
                           zerophase=True)
        appTraceHigh.trim(ts,te)

        s = np.asarray(self.get_all_nslc())
        for network in np.unique(s[:, 0]):
            for station in np.unique(s[:, 1]):
                nTr = network + '_' + station
                try:
                    print('amplitude analisys '+station)
                    stTrace = appTraceLow.select(network, station)
                    envL =[obspy.signal.filter.envelope(st.data) for st in stTrace]
                    if np.max([np.max(e) for e in envL])>self._amplAn['lowFTh']:
                        a = alert(table)
                        a._time = te
                        # a._a['utc_time'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
                        # a._a['utc_time_str'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
                        a._a['event_type'] = "'AML'"
                        a._a['station'] = "'" + nTr + "'"
                        a._a['amplitude_ehe'] = np.max(envL[0])
                        a._a['amplitude_ehn'] = np.max(envL[1])
                        a._a['amplitude_ehz'] = np.max(envL[2])
                        a.insert()


                    stTrace = appTraceHigh.select(network, station)
                    envH = [obspy.signal.filter.envelope(st.data) for st in stTrace]
                    if np.max([np.max(e) for e in envH]) > self._amplAn['highFTh']:
                        a = alert(table)
                        a._time = te
                        a._a['event_type'] = "'AMH'"
                        a._a['station'] = "'" + nTr + "'"
                        a._a['amplitude_ehe'] = np.max(envH[0])
                        a._a['amplitude_ehn'] = np.max(envH[1])
                        a._a['amplitude_ehz'] = np.max(envH[2])
                        a.insert()

                except:
                    print('amplitude analisys '+station+ ' failed')
                    pass

        self._elRunning = False

    # def multiAmplitudeRawAn(self):
    #     for st in self._sysStations._stations.keys():
    #         stName=self._sysStations._stations[st]._name
    #         multiprocessing.Process(target=self.amplitudeRawAn, name=st, args=(self._sysStations._network,stName,)).start()
    #
    # def amplitudeRawAn(self,network,station):
    #
    #     l = log()
    #     te = l.rdLog()
    #
    #     sft=np.int(self._amplAn['sft']*3600)
    #     wnd=np.int(self._amplAn['wnd']*3600)
    #     while True:
    #         try:
    #             lastTime=np.min([UTCDateTime(self._get_current_endtime(network,station,'',ch )) for ch in ['EHZ','EHN','EHZ']])
    #             print('amplitude analisys try' + station + ' lt:' + str(lastTime) + ' te:' + str(te))
    #             stName=network + "_" + station
    #             self._sysStations.updateLatency(stName, np.int(UTCDateTime.now()-lastTime))
    #             if lastTime>te+86400:
    #                 te=lastTime
    #
    #             teMax=te+wnd/2
    #             teMin = te - wnd / 2
    #
    #             if teMax<lastTime-wnd/2:
    #                 print('amplitude analisys ' + stName + ' lt:' + str(lastTime) + ' te:' + str(te))
    #                 tr = self.get_waveforms(network, station, '', 'EH?', te - wnd,
    #                                         te + wnd)
    #                 tr.merge(fill_value=0)
    #                 tr.remove_response(self._inv)
    #
    #
    #
    #                 appTraceLow = tr.copy()
    #                 appTraceLow.filter('bandpass', freqmin=self._amplAn['lowFW'][0], freqmax=self._amplAn['lowFW'][1], corners=3,
    #                                 zerophase=True)
    #                 appTraceLow.trim(teMin, teMax)
    #
    #                 appTraceHigh =tr.copy()
    #                 appTraceHigh.filter('bandpass', freqmin=self._amplAn['highFW'][0], freqmax=self._amplAn['highFW'][1], corners=3,
    #                                    zerophase=True)
    #                 appTraceHigh.trim(teMin, teMax)
    #
    #                 envL =[obspy.signal.filter.envelope(st.data) for st in appTraceLow]
    #                 ee=envL[0]
    #                 en=envL[1]
    #                 ez=envL[2]
    #                 am = np.sqrt(ee ** 2 + en ** 2 + ez ** 2)
    #                 if np.max(am)>self._amplAn['lowFTh']:
    #                     a = alert(self._alertTable)
    #                     a._time = te
    #                     a._a['event_type'] = "'AML'"
    #                     a._a['station'] = "'" + stName + "'"
    #                     a._a['amplitude_ehe'] = np.max(ee)
    #                     a._a['amplitude_ehn'] = np.max(en)
    #                     a._a['amplitude_ehz'] = np.max(ez)
    #                     a._a['median_amplitude']=np.median(am)
    #                     a._a['max_amplitude']=np.max(am)
    #                     r=np.diff((am>self._amplAn['lowFTh'])*1)
    #                     a._a['rate']=len(r[r>0])
    #                     a.insert()
    #
    #
    #                 envH = [obspy.signal.filter.envelope(st.data) for st in appTraceHigh]
    #                 ee = envH[0]
    #                 en = envH[1]
    #                 ez = envH[2]
    #                 am = np.sqrt(ee ** 2 + en ** 2 + ez ** 2)
    #                 if np.max(am) > self._amplAn['highFTh']:
    #                     a = alert(self._alertTable)
    #                     a._time = te
    #                     a._a['event_type'] = "'AMH'"
    #                     a._a['station'] = "'" + stName + "'"
    #                     a._a['amplitude_ehe'] = np.max(ee)
    #                     a._a['amplitude_ehn'] = np.max(en)
    #                     a._a['amplitude_ehz'] = np.max(ez)
    #                     a._a['median_amplitude'] = np.median(am)
    #                     a._a['max_amplitude'] = np.max(am)
    #                     r = np.diff((am > self._amplAn['lowFTh']) * 1)
    #                     a._a['rate'] = len(r[r > 0])
    #                     a.insert()
    #                 te = te + sft
    #                 l.wrLog(te)
    #
    #             else:
    #                 time.sleep(np.int(sft/2))
    #
    #         except:
    #             print('amplitude analisys '+stName+ ' failed')
    #             te=te+sft
    #             time.sleep(sft)
    #             l.wrLog(te)


    def getLastTime(self,network,station):
        stName = network + "_" + station
        lastTime=0
        try:
            lastTime=np.min([UTCDateTime(self._get_current_endtime(network,station,'',ch )) for ch in ['EHZ','EHN','EHZ']])
        except:
            pass
        self._sysStations.updateLatency(stName, np.int(UTCDateTime.now() - lastTime))
        return lastTime


    def amplitudeRawAn(self,te,network,station):
        stName = network + "_" + station

        wnd=np.int(self._amplAn['wnd']*3600)

        teMax=te-10
        teMin = te - 10-wnd

        try:
            print('amplitude analisys ' + stName + ' lt:' + str(teMin) + ' te:' + str(teMax))
            tr = self.get_waveforms(network, station, '', 'EH?', te -20-wnd,
                                    te)
            tr.merge(fill_value=0)
            tr.remove_response(self._inv)

            appTraceLow = tr.copy()
            appTraceLow.filter('bandpass', freqmin=self._amplAn['lowFW'][0], freqmax=self._amplAn['lowFW'][1], corners=3,
                            zerophase=True)
            appTraceLow.trim(teMin, teMax)

            appTraceHigh =tr.copy()
            appTraceHigh.filter('bandpass', freqmin=self._amplAn['highFW'][0], freqmax=self._amplAn['highFW'][1], corners=3,
                               zerophase=True)
            appTraceHigh.trim(teMin, teMax)

            envL =[obspy.signal.filter.envelope(st.data) for st in appTraceLow]
            ee=envL[0]
            en=envL[1]
            ez=envL[2]
            am = np.sqrt(ee ** 2 + en ** 2 + ez ** 2)
            ambins = [np.max(am[aa:aa + self._rsp]) for aa in np.arange(0, len(am) - 1, self._rsp)]
            amA=np.asarray(ambins)
            amA = amA[amA > self._amplAn['lowFTh']]
            if len(amA)>0:
                a = alert(self._alertTable)
                a._time = te
                a._a['event_type'] = "'AML'"
                a._a['station'] = "'" + stName + "'"
                a._a['amplitude_ehe'] = np.max(ee)
                a._a['amplitude_ehn'] = np.max(en)
                a._a['amplitude_ehz'] = np.max(ez)
                a._a['median_amplitude']=np.median(amA)
                a._a['max_amplitude']=np.max(amA)
                a._a['mean_amplitude'] = np.mean(amA)
                a._a['rate']=len(amA)
                a.insert()


            envH = [obspy.signal.filter.envelope(st.data) for st in appTraceHigh]
            ee = envH[0]
            en = envH[1]
            ez = envH[2]
            am = np.sqrt(ee ** 2 + en ** 2 + ez ** 2)
            ambins = [np.max(am[aa:aa + self._rsp]) for aa in np.arange(0, len(am) - 1, self._rsp)]
            amA = np.asarray(ambins)
            amA = amA[amA > self._amplAn['highFTh']]
            if len(amA)>0:
                a = alert(self._alertTable)
                a._time = te
                a._a['event_type'] = "'AMH'"
                a._a['station'] = "'" + stName + "'"
                a._a['amplitude_ehe'] = np.max(ee)
                a._a['amplitude_ehn'] = np.max(en)
                a._a['amplitude_ehz'] = np.max(ez)
                a._a['median_amplitude'] = np.median(amA)
                a._a['max_amplitude'] = np.max(amA)
                a._a['rate'] = len(amA)
                a.insert()
        except:
            print('amplitude analisys ' + stName + ' lt:' + str(teMin) + ' te:' + str(teMax)+' failed, no data')


    def run(self, network, station, channel):
        logging.basicConfig(filename='log.log', level='WARNING',format='%(asctime)s %(message)s')

        l=log()
        tStart=l.rdLog()

        self._stationData={
            'BRK0': self._inv.get_coordinates('LK.BRK0..EHZ'),
            'BRK1': self._inv.get_coordinates('LK.BRK1..EHZ'),
            'BRK2': self._inv.get_coordinates('LK.BRK2..EHZ'),
            'BRK3': self._inv.get_coordinates('LK.BRK3..EHZ'),
            'BRK4': self._inv.get_coordinates('LK.BRK4..EHZ'),
        }

        # with open(self._basePathRT+'elab_status.json', 'w') as fp:
        #     json.dump(self._stationData, fp)
        #     fp.close()

        self._tNow=tStart
        a=alert(self._alertTable)
        while 1 < 2:

            if self._tNow>UTCDateTime.now()-5:
                time.sleep(5)
                self._tNow = UTCDateTime.now()
                rt=True
                print(self._tNow)
            else:
                self._tNow += 10
                print(self._tNow)
                rt=False



            if self._tNow.second < self._lastData.second:
                self._tEnd = self._tNow
                # try:
                #     with urllib.request.urlopen("http://worldtimeapi.org/api/timezone/America/Maceio") as url:
                #         data = json.loads(url.read().decode())
                #         self._localTimeOffset=np.int(data['dst_offset'])+np.int(data['raw_offset'])
                # except:
                #     pass

                print('getting traces')
                try:
                    self._traces = self.get_waveforms(network, station, '', channel, self._tEnd - 720 * 60,
                                                      self._tEnd)
                    self._traces.merge(fill_value=0)
                    self._log['lastRcv']=self._tEnd
                except:
                    print('failed to get traces')

                self._2minRTraces = self._traces.copy()
                self._2minRTraces.trim(self._tEnd - 120, self._tEnd)
                self._2minRTraces.remove_response(self._inv)
                self._2minRTraces.sort()

                # self._sysStations._raw=self._2minRTraces.copy()
                print('traces ok')
                if (not self._elRunning):
                    print('an start')
                    self.An(self._alertTable)
                    print('an done')
                if (self._tNow.minute % self._rtSft == 0) & (self._lastData.minute % self._rtSft != 0):
                    print('getting ev')
                    a.getAlerts(self._tEnd-3600*24,self._tEnd,'*','CASP')
                    self._events=[dict(time=UTCDateTime(aa['utc_time'])+self._localTimeOffset, text='CASP ev. mag' + str(aa['magnitudo'])) for aa in a._aList]
                    print('ev done')
                    if (not self._rtRunning) & rt:

                        pRt = multiprocessing.Process(target=self.realTimeDrumPlot)
                        pRt.start()


                if (self._tEnd.minute == 0) & (self._lastData.minute != 0):
                    if not self._hyRunning:
                        pHy = multiprocessing.Process(target=self.hystDrumPlot)
                        pHy.start()

                l.wrLog(self._tEnd)
            self._lastData = self._tNow


    def runAcq(self,tBufShort=120,tBufLong=720*60):

        l=log()
        self._tNow=l.rdLog()
        k=self._sysStations._stations.keys()
        network=self._sysStations._stations[k[0]]._network
        station=[self._sysStations._stations[st]._name for st in self._sysStations._stations.keys()]

        channel="EH?"

        while True:

            if self._tNow>UTCDateTime.now()-5:
                time.sleep(5)
                self._tNow = UTCDateTime.now()
            else:
                self._tNow += 10


            if self._tNow.second < self._lastData.second:
                self._tEnd = self._tNow

                print('getting traces'+ UTCDateTime(self._tEnd).strftime("%Y-%m-%d %H:%M:%S"))
                for s in station:
                    try:
                        self._traces+=self.get_waveforms(network, s, '', channel, self._tEnd - tBufLong,
                                                          self._tEnd)
                        self._traces.merge(fill_value=0)
                    except:
                        print('failed to get traces')

                s = self._traces.copy()
                s.trim(self._tEnd - tBufShort, self._tEnd)
                s.remove_response(self._inv)
                s.sort()
                try:
                    self._sysStations._raw[0]=s.copy()
                except:
                    self._sysStations._raw.append(s.copy())

                l.wrLog(self._tEnd)
            self._lastData = self._tNow


    def getCasp(self):
        try:
            connection = psycopg2.connect(host='172.16.8.10', port='5432', database='casp_events', user='sismoweb',
                                          password='lun1t3k@@',connect_timeout=10)
            sql = 'SELECT event_id, t0, lat, lon, dpt, magWA,reliable,erh,erz FROM auto_eventi ORDER BY event_id DESC LIMIT 10'
            cursor = connection.cursor()
            cursor.execute(sql)
            p = cursor.fetchall()
        except:
            print('get CASP failed')
            pass
        a = alert()

        for pp in p:
            a._time =UTCDateTime(pp[1])
            a._a['event_type'] = "'CASP'"
            a._a['station'] = "'*'"
            a._a['lat'] =np.float(pp[2])
            a._a['lon'] = np.float(pp[3])
            a._a['magnitudo'] = np.float(pp[5])
            a._a['depth'] = np.float(pp[4])
            a._a['id_casp'] = pp[0]
            a._a['rel'] = pp[6]
            a._a['erh'] = pp[7]
            a._a['erz'] = pp[8]
            a.insert(False)
        connection.close()

    def getCaspTime(self,te):
        p=[]
        try:
            ts=te-self._rTh['wnd']*3600
            connection = psycopg2.connect(host='172.16.8.10', port='5432', database='casp_events', user='sismoweb',
                                          password='lun1t3k@@',connect_timeout=10)
            sql = "SELECT event_id, t0, lat, lon, dpt, magWA,reliable,erh,erz FROM auto_eventi where t0>'"+ts.strftime("%Y-%m-%d %H:%M:%S")+"'and t0<'"+te.strftime("%Y-%m-%d %H:%M:%S")+"' order by t0 asc;"
            cursor = connection.cursor()
            cursor.execute(sql)
            p = cursor.fetchall()
            print('get CASP '+UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S"))
            connection.close()

        except:
            print('get CASP failed')
            pass
        a = alert(self._alertTable)

        for pp in p:
            a._time =UTCDateTime(pp[1])
            a._a['event_type'] = "'CASP'"
            a._a['station'] = "'*'"
            a._a['lat'] =np.float(pp[2])
            a._a['lon'] = np.float(pp[3])
            a._a['magnitudo'] = np.float(pp[5])
            a._a['depth'] = np.float(pp[4])
            a._a['id_casp'] = pp[0]
            a._a['rel'] = pp[6]
            a._a['erh'] = pp[7]
            a._a['erz'] = pp[8]
            a.insert(False)


    def rawCASP(self,te):
        self.getCaspTime(te)
        self.rtAlertCASP(te)

    def rtAlertCASP(self,te):
        a=alert(self._alertTable)
        a.getAlerts(te-self._rTh['wnd']*3600,te,'*','CASP')
        for aa in a._aList:
            if aa['magnitudo'] > self._rTh['CASP']:  # self._rTh['sft']
                self._sysStations.insertAlert(aa['utc_time'], aa['station'], "'"+aa['event_type']+"'", 4,
                                               self._rTh['alON'] * 3600, 'High magnitudo CASP event')



    def pushIntEv(self,e,table='seismic.events_swarm',id='id_swarm'):
        connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
                                      password='Bebedouro77627')
        #for e in events:

        sql = 'INSERT INTO '+table+ ' (geom,note,lat,lon,utc_time,utc_time_str,magnitudo,depth,'+id+') ' \
              "VALUES (ST_GeomFromText('POINT(" + str(e['lon']) + ' ' + str(e['lat']) + ")', 4326)" \
              + ",'" + e['note'] + "'," + str(e['lat']) + ',' + str(e['lon']) + ",'" + str(
            UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S")) + "','" + str(
            UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S")) + "'," + str(e['mag']) + ',' + str(e['dpt']) + ",'" + \
              e['id'] + "') ON CONFLICT DO NOTHING;"
        connection.cursor().execute(sql)
        connection.commit()
