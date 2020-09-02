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



st=['LK_BRK0','LK_BRK1','LK_BRK2','LK_BRK3','LK_BRK4']
cl=[('LK_BRK0','LK_BRK1'),('LK_BRK1','LK_BRK2')]
te=UTCDateTime(2020,8,26,4,0,0)

al._a['utc_time'] = "'" + UTCDateTime(te-600).strftime("%Y-%m-%d %H:%M:%S")  + "'"
al._a['utc_time_str'] = "'" + UTCDateTime(te-600).strftime("%Y-%m-%d %H:%M:%S")  + "'"
al._a['event_type'] = "'HR_AMT'"
al._a['station'] = "'LK_BRK0'"
al._a['level'] = 1
al.insert()
al._a['utc_time'] = "'" + UTCDateTime(te-200).strftime("%Y-%m-%d %H:%M:%S")  + "'"
al._a['utc_time_str'] = "'" + UTCDateTime(te-200).strftime("%Y-%m-%d %H:%M:%S")  + "'"
al._a['event_type'] = "'HR_AMT'"
al._a['station'] = "'LK_BRK1'"
al._a['level'] = 2
al.insert()

al.clusterStation(te,cl,3600,'HR_AMT')



