from obspy import UTCDateTime
import json
import multiprocessing
import time
import numpy as np


class log():

    _lastElaborate=UTCDateTime

    def rdLogCluster(self, pName=[]):

        try:
            for pp in pName:
                with open(pp + '.json', 'r') as fp:
                    p = json.load(fp)
                    self._lastElaborate = UTCDateTime.strptime(p['last'], "%Y-%m-%d %H:%M:%S")
                    fp.close()
                    te = self._lastElaborate
        except:
            te = UTCDateTime.now()
            pass
        return te

    def rdLog(self,pName=''):
        if pName=='':
            pName = multiprocessing.current_process().name
        try:
            with open(pName+'.json', 'r') as fp:
                p=json.load(fp)
                self._lastElaborate=UTCDateTime.strptime(p['last'],"%Y-%m-%d %H:%M:%S")
                fp.close()
                te=self._lastElaborate
        except:
            te=UTCDateTime.now()
            pass
        return te



    def wrLog(self,t):
        pName = multiprocessing.current_process().name
        self._lastElaborate=t
        with open(pName+'.json', 'w') as fp:
            tstr=self._lastElaborate.strftime("%Y-%m-%d %H:%M:%S")
            s={
                'last':tstr
            }
            json.dump(s, fp)
            fp.close()
            #print('saved '+pName+' '+tstr)



class sch:

    _lastProcessedTime=UTCDateTime
    _actualElaborationTime=UTCDateTime
    _maxElaborationTime=UTCDateTime
    _sft=5/3600
    _maxTFnc=object
    _maxTArgs=object
    l=log
    p=''


    def __init__(self,sft,p,tForce,maxTFnc,maxTArgs=[]):
        self.l=log()
        self.p=p
        if self.p=='':
            self.p = multiprocessing.current_process().name
        if tForce==0:
            self._lastProcessedTime=self.l.rdLog(self.p)
        else:
            self._lastProcessedTime =tForce
        self._lastProcessedTime.second=0
        self._sft=np.int(sft*3600)
        if self._sft<2:
            raise Exception('Tooo shoortt sft!!')
        self._maxTFnc=maxTFnc
        self._maxTArgs=maxTArgs


    def schRun(self,fnc,args):

        self._actualElaborationTime=self._lastProcessedTime
        pName = multiprocessing.current_process().name
        while True:
            if len(self._maxTArgs)==0:
                self._maxElaborationTime=self._maxTFnc()
            else:
                self._maxElaborationTime = self._maxTFnc(*self._maxTArgs)
            if self._actualElaborationTime>self._maxElaborationTime:
                time.sleep(np.int(self._sft/2))
            else:
                #to do
                fnc(self._actualElaborationTime,*args)
                self._actualElaborationTime+=self._sft
                self.l.wrLog(self._actualElaborationTime)






def uuu(t):
    print(t)

print('o')
print('p')