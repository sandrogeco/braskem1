import matplotlib.pyplot as plt
plt.switch_backend('agg')
import os
import logging
from obspy import UTCDateTime
from obspy.core.stream import Stream
from obspy.clients.filesystem.sds import Client

import multiprocessing
from multiprocessing import Event
import obspy.signal.polarization
from obspy import read_inventory
import obspy.signal


import json
import psycopg2
import time
import numpy as np



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

# class stations():
#     _stations={}
#     def __init__(self,sts,net,table='seismic.stations'):
#
#         for s in sts:
#             self._stations[net+"_"+s]=station(s,net)
#
#         self._table = table
#
#
#     def updateStationLatency(self):
#         self.connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
#                                        password='Bebedouro77627')
#         for station in self._stations.values():
#             station.update()
#             sql = "update "+self._table+" set latency=" + str(station._latency) +", status=" + str(station._status)+" where name='" + str(
#                 station._intName) + "';"
#             self.connection.cursor().execute(sql)
#             self.connection.commit()
#
#         self.connection.close()
#
#     def updateStationStatus(self):
#
#         self.connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
#                                        password='Bebedouro77627')
#         for station in self._stations.values():
#             station.update()
#             sql = "update "+self._table+" set status=" + str(station._status) +  " where name='" + str(
#                 station._intName) + "';"
#             print(sql)
#             self.connection.cursor().execute(sql)
#             self.connection.commit()
#
#         self.connection.close()
#
#
# class station():
#     _CL_HR=0
#     _HR=0
#     _status=1
#     _latency=0
#     _name=''
#     _network=''
#     _intName=''
#     _maxLatency=15
#
#
#     def __init__(self,name,net):
#         self._name=name
#         self._network=net
#         self._intName=self._network+"_"+self._name
#
#
#
#     def update(self):
#
#         if self._latency>self._maxLatency:
#             self._status=0
#         else:
#             self._status=self._CL_HR+1
#

class sysStations():

    def __init__(self,sts,net,table='seismic.stations'):
        self._stations=multiprocessing.Manager().dict()
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

        # if a._latency > a._maxLatency:
        #     a._status = 0
        # else:
        #     a._status =a._CL_HR + 1
        #
        # self._stations[key]=a
        # self.updateDB(a)
    #
    # def updateAllStz(self,*args):#key,attr,value):
    #     for s in self._stations:
    #         key=s._intName
    #         if len(args)==1:
    #             a=args[0]
    #             #key=a._intName
    #
    #         if len(args)==3:
    #             #key=args[0]
    #             attr=args[0]
    #             value=args[1]
    #             a=self._stations[key]
    #             a.__setattr__(attr,value)
    #
    #         self.statusCalc(a, key)

    def statusCalc(self,a,key):
        if a._latency > a._maxLatency:
            a._status = 0
        else:
            l=np.max([a._CL_HR,a._HR,a._AM,a._MAG])
            a._status = l + 1

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
            print('DB update failed')
            pass

class sysStation():
    _CL_HR=0
    _HR=0
    _AM=0
    _MAG=0
    _lastAlertType=''
    _lastAlertTime=UTCDateTime
    _status=1
    _latency=0
    _name=''
    _network=''
    _intName=''
    _maxLatency=15


    def __init__(self,name,net):
        self._name=name
        self._network=net
        self._intName=self._network+"_"+self._name



class alert():
    # _stations=stations
    _sysStations=sysStations
    _confFile='pp.json'
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
        'erz':0
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

    def __init__(self,table=''):
        self.connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
                                      password='Bebedouro77627')
        self._table=table

    def __del__(self):
        self.connection.close()


    def insert(self,s0=True,clause=''):
        try:
            t=UTCDateTime.strptime(self._a['utc_time'],"'%Y-%m-%d %H:%M:%S'")
            if s0:
                self._a['utc_time']=t.strftime("'%Y-%m-%d %H:%M:00'")
                self._a['utc_time_str']=t.strftime("'%Y-%m-%d %H:%M:00'")
            else:
                self._a['utc_time'] = t.strftime("'%Y-%m-%d %H:%M:%S'")
                self._a['utc_time_str'] = t.strftime("'%Y-%m-%d %H:%M:%S'")
            sql = "INSERT INTO " + self._table + " ("+"".join(str(s) + "," for s in self._a.keys())
            sql = sql[0:-1]
            sql += ") SELECT "+"".join( str(s) + "," for s in self._a.values())
            sql = sql[0:-1]
            sql += " WHERE NOT EXISTS( SELECT * FROM " + self._table + " WHERE utc_time=" + self._a['utc_time'] + \
                   " AND  station=" + self._a['station'] + " AND event_type=" + self._a['event_type'] + ");"
            self.connection.cursor().execute(sql)
            self.connection.commit()
        except:
            pass


    def getAlerts(self,ts,te,station='', event_type='',extra=''):
        r = False
        try:
            sql="SELECT "+"".join(str(s) + "," for s in self._a.keys())
            sql = sql[0:-1]

            sql+=" FROM "+self._table+ " WHERE station='"+station+"' AND event_type='"+event_type+\
                "' AND utc_time>'"+UTCDateTime(ts).strftime("%Y-%m-%d %H:%M:%S")+\
            "' AND utc_time<'"+UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S")+"' "+extra+" ;"
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
        print(te)
        r=False
        ts=te-3600*self._rTh['wnd']
        self.getAlerts(ts,te,station,type)
        aa=[]
        for a in self._aList:
            if a['magnitudo']>self._th[type]:
                aa.append(a)

        if len(aa)>self._rTh[type]:
            self._a['utc_time'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
            self._a['utc_time_str'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
            self._a['event_type'] = "'HR_"+type+"'"
            self._a['rate'] = len(aa)/self._rTh['wnd']
            ampl = np.mean(self._a['magnitudo'])
            fR = np.where(self._rateX >= self._a['rate'])[0]
            fA = np.where(self._amplY <= ampl)[0]
            fR = fR[0]
            fA = fA[0]
            self._a['level'] = np.int(self._thMatrix[fA, fR])
            print(type+' '+station+' '+str(self._a['rate'])+' '+str(self._a['level']))
            self.insert()
            # self._sysStations.updateStz(station, '_CL_HR', l)
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
        #print('al'+str(len(self._aList)))
        if len(aa)>self._rTh[type]:
            self._a['utc_time'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
            self._a['utc_time_str'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
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


    def HR_run(self,st,aType):
        try:
            with open('lastDet.json', 'r') as fp:
                p=json.load(fp)
                self._log={k: UTCDateTime.strptime(p[k],"%Y-%m-%d %H:%M:%S") for k in p}
                fp.close()
                te=self._log['lastElab']
        except:
            te=UTCDateTime.now()
            pass

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

                self._log['lastElab']=te
                te=te+self._rTh['sft']*3600

            else:
                time.sleep(10)


            with open('lastDet.json', 'w') as fp:
                s = {k: self._log[k].strftime("%Y-%m-%d %H:%M:%S") for k in self._log}
                json.dump(s, fp)
                fp.close()

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
                    self._a['utc_time'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
                    self._a['utc_time_str'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
                    self._a['event_type'] = "'CL_" + evType + "'"
                    self._a['station'] = "'" + st + "'"
                    self._a['level'] = l
                    self.insert()
            self._sysStations.updateStz(st,'_CL_HR',l)

        # for sts in self._stations._stations.keys():
        #     if self.getAlerts(te - np.int(lag), te, sts, 'CL_HR_AML'):
        #         l = np.max([a['level'] for a in self._aList])
        #     else:
        #         l=0
        #     self._stations._stations[sts]._CL_HR=l
        # self._stations.updateStationStatus()


class drumPlot(Client):

    _log={
        'lastRcv':  UTCDateTime.now(),
        'lastCASP': UTCDateTime.now(),
        'lastDrum': UTCDateTime.now(),
    }


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
    _polAn={
        'polWinLen':5,
        'polWinFr':.1,
        'fLow':4,
        'fHigh':12,
        'plTh':0.000005#0.8
    }
    _amplAn = {
        'lowFW': [1,20],
        'highFW': [20,50],
        'lowFTh': 0.00001,
        'highFTh': 0.00005

    }

    _polAnResult=[]





    def plotDrum(self, trace, filename='tmp.png'):
        #print(trace.get_id())
        try:
            trace.data = trace.data * 1000 / 3.650539e+08
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            trace.plot(type='dayplot',
                            dpi=dpi,
                            x_labels_size=int(8 * 100 / int(dpi)),
                            y_labels_size=int(8 * 100 / int(dpi)),
                            title_size=int(1000 / int(dpi)),
                            title=self._tEnd.strftime("%Y/%m/%d %H:%M:%S"),
                            size=(sizex, sizey),
                            color=('#AF0000', '#00AF00', '#0000AF'),
                            vertical_scaling_range=yRange,
                            outfile=filename,
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
                self._sysStations.updateStz(network+"_"+station,'_latency',l)
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

    def hystDrumPlot(self,tEnd=0):

        appTrace = Stream()
        self._hyRunning = True
        if tEnd==0:
            tEnd=self._tEnd
        else:
            self._tEnd=tEnd
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
                        appTrace.trim(tStart, tEnd, pad=True, fill_value=0)
                        appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                        self.plotDrum(appTrace, self._basePath + fileName)
        self._hyRunning = False



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
                        a._a['utc_time'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
                        a._a['utc_time_str'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
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
                        a._a['utc_time'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
                        a._a['utc_time_str'] = "'" + UTCDateTime(te).strftime("%Y-%m-%d %H:%M:%S") + "'"
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

    def polAn(self,stTrace,ts,te,nTr,env,table):

        u = obspy.signal.polarization.polarization_analysis(
            stTrace, self._polAn['polWinLen'],
            self._polAn['polWinFr'],
            self._polAn['fLow'],
            self._polAn['fHigh'],
            ts, te, False, 'pm',self._polAn['plTh']**2)

        x = np.where(u['azimuth_error'] > 0.01)#self._polAn['plTh'])
        a = alert(table)

        for xx in x[0]:
            a._a['utc_time'] = "'" + UTCDateTime(u['timestamp'][xx]).strftime(
                "%Y-%m-%d %H:%M:%S") + "'"
            a._a['utc_time_str'] = "'" + UTCDateTime(u['timestamp'][xx]).strftime(
                "%Y-%m-%d %H:%M:%S") + "'"
            a._a['event_type'] = "'PL'"
            a._a['station'] = "'" + nTr + "'"
            #a._a['linearity'] = u['planarity'][xx]
            a._a['az'] = u['azimuth'][xx]
            a._a['tkoff'] = u['incidence'][xx]
            y = np.where(
                (u['timestamp'][xx] - self._polAn['polWinLen'] < stTrace[0].times('timestamp')) &
                (stTrace[0].times('timestamp') <= u['timestamp'][xx]))
            a._a['amplitude_ehe'] = np.max(env[0][y])
            a._a['amplitude_ehn'] = np.max(env[1][y])
            a._a['amplitude_ehz'] = np.max(env[2][y])
            # print(a._a)

            a.insert()



    def run(self, network, station, channel):
        logging.basicConfig(filename='log.log', level='WARNING',format='%(asctime)s %(message)s')
        tStart = UTCDateTime()
        try:
            with open('lastRaw.json', 'r') as fp:
                p=json.load(fp)
                self._log={k: UTCDateTime.strptime(p[k],"%Y-%m-%d %H:%M:%S") for k in p}
                fp.close()
                tStart = self._log['lastRcv']
        except:
            tStart=UTCDateTime.now()
            pass


        self._stationData={
            'BRK0': self._inv.get_coordinates('LK.BRK0..EHZ'),
            'BRK1': self._inv.get_coordinates('LK.BRK1..EHZ'),
            'BRK2': self._inv.get_coordinates('LK.BRK2..EHZ'),
            'BRK3': self._inv.get_coordinates('LK.BRK3..EHZ'),
            'BRK4': self._inv.get_coordinates('LK.BRK4..EHZ'),
        }

        with open(self._basePathRT+'elab_status.json', 'w') as fp:
            json.dump(self._stationData, fp)
            fp.close()

        self._tNow=tStart
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

                if (not self._elRunning):
                    self.An(self._alertTable)

                if (self._tNow.minute % self._rtSft == 0) & (self._lastData.minute % self._rtSft != 0):
                    print('getting events')
                    try:
                        self.getCasp()
                        self.pushEv()
                        self._log['lastCASP']=self._tEnd

                    except:
                        print('CASP events forwarding failed')
                        pass


                    if (not self._rtRunning) & rt:
                        pRt = multiprocessing.Process(target=self.realTimeDrumPlot)
                        pRt.start()

                if (self._tEnd.minute == 0) & (self._lastData.minute != 0):
                    if not self._hyRunning:
                        pHy = multiprocessing.Process(target=self.hystDrumPlot)
                        pHy.start()


                with open('lastRaw.json', 'w') as fp:
                    s = {k: self._log[k].strftime("%Y-%m-%d %H:%M:%S") for k in self._log}
                    json.dump(s, fp)
                    fp.close()
                    print('saved')

            self._lastData = self._tNow

    def getCasp(self):
        connection = psycopg2.connect(host='172.16.8.10', port='5432', database='casp_events', user='sismoweb',
                                      password='lun1t3k@@',connect_timeout=10)
        sql = 'SELECT event_id, t0, lat, lon, dpt, magWA,reliable,erh,erz FROM auto_eventi ORDER BY event_id DESC LIMIT 10'
        cursor = connection.cursor()
        cursor.execute(sql)
        p=cursor.fetchall()
        self._events=[]
        for pp in p:
            e={
                'id':pp[0],
                'time':UTCDateTime(pp[1]),
                'text':'CASP ev. mag'+str(pp[5]),
                'lat':np.float(pp[2]),
                'lon':np.float(pp[3]),
                'dpt':np.float(pp[4]),
                'mag':np.float(pp[5]),
                'rel':pp[6],
                'erh':np.float(pp[7]),
                'erz':np.float(pp[8])
            }
            self._events.append(e)

    def pushEv(self):
        connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
                                      password='Bebedouro77627')
        for e in self._events:

            sql = 'INSERT INTO seismic.events_casp (geom,lat,lon,utc_time,utc_time_str,magnitudo,depth,id_casp,rel) ' \
                  "VALUES (ST_GeomFromText('POINT(" + str(e['lon']) + ' ' + str(e['lat']) + ")', 4326),"\
                  + str(e['lat']) + ','+ str(e['lon'])+ ",'"+  str(UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S"))+ "','"+  str(UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S"))+"',"+str(e['mag'])+','+ str(e['dpt'])  +','+e['id']+","+str(e['rel'])+") ON CONFLICT DO NOTHING;"
            connection.cursor().execute(sql)
            connection.commit()
            connection.close()
            #

            a = alert()
            a._a['utc_time'] = "'" + UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S") + "'"
            a._a['utc_time_str'] = "'" + UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S") + "'"
            a._a['event_type'] = "'CASP'"
            a._a['station'] = "'*'"
            a._a['lat'] =e['lat']
            a._a['lon'] = e['lon']
            a._a['magnitudo'] = e['mag']
            a._a['depth'] = e['dpt']
            a._a['id_casp'] = e['id']
            a._a['rel'] = e['rel']
            a._a['erh'] = e['erh']
            a._a['erz'] = e['erz']
            a.insert(False)
            #
            # sql='INSERT INTO seismic.alerts (station,lat,lon,utc_time,utc_time_str,magnitudo,depth,id_casp,rel,event_type)'\
            #    " SELECT '*',"+ str(e['lat']) + ','+ str(e['lon'])+ ",'"+  str(UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S"))+ "','"+  str(UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S"))+"',"+str(e['mag'])+','+ str(e['dpt'])  +','+e['id']+","+str(e['rel'])+\
            #    ",'CASP' WHERE NOT EXISTS( SELECT * FROM seismic.alerts  WHERE id_casp="+e['id'] + ");"
            # connection.cursor().execute(sql)
            # connection.commit()



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
