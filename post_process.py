# start 10.30
#!pippo2010
# sudo ./slarchive -v -SDS /mnt/ide/seed/ -x statefile -S LK_BRK?:EH? 172.16.8.10:18000

# openvpn --config clientBRASKEM__GEOAPP.conf
#
# #sudo sshfs -o allow_other braskem@80.211.98.179:/uploads /mnt/geoAppServer/



from seisLib import drumPlot
from seisLib import alert


from obspy import  UTCDateTime
import numpy as np

al=alert('seismic.alerts')

te=UTCDateTime(2020,8,26,4,0,0)

st=['LK_BRK0','LK_BRK1','LK_BRK2','LK_BRK3','LK_BRK4']
cl=[('LK_BRK0','LK_BRK2'),('LK_BRK1','LK_BRK2'),('LK_BRK1','LK_BRK4'),('LK_BRK3','LK_BRK4')]

al._rateX=np.arange(0,100,1)
al._amplY=np.arange(0.01,-0.0001,-0.0001)
al._thMatrix=np.zeros([len(al._amplY),len(al._rateX)])
al._thMatrix[0:np.where(al._amplY>0.0003)[0][-1],5:]=1
al._thMatrix[0:np.where(al._amplY>0.0008)[0][-1],20:]=2
al._thMatrix[0:np.where(al._amplY>0.002)[0][-1],40:]=3
al._clusters=cl
al.HR_run(st,te)

