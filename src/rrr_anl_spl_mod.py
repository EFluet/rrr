#!/usr/bin/python
#*******************************************************************************
#rrr_anl_spl_mod.py
#*******************************************************************************
#Purpose:
#This script sumbsamples river model outputs based on prior subsampling of
#the river network based on polygons and their mean times.
#Author:
#Etienne Fluet Chouinard, Cedric H. David, 2016-2016


#*******************************************************************************
#Import Python modules
#*******************************************************************************
import sys
import csv
import netCDF4
import datetime
import calendar
import numpy


#*******************************************************************************
#Domain specific hard-coded variables in case metadata is missing for netCDF
#*******************************************************************************
iso_str_date='1970-01-01T00:00:00'
#The beginning time of the first time step in the input netCDF file.
#ISO 8601 format: '1970-01-01T00:00:00', make sure UTC is used 
ZS_TauR=10800
#The duration (s) of the time steps in the input netCDF files, 3h is most common


#*******************************************************************************
#Declaration of variables (given as command line arguments)
#*******************************************************************************
# 1 - rrr_mod_nc1
# 2 - rrr_spl_csv
# 3 - rrr_mod_nc2


#*******************************************************************************
#Get command line arguments
#*******************************************************************************
IS_arg=len(sys.argv)
if IS_arg != 4:
     print('ERROR - 3 and only 3 arguments can be used')
     raise SystemExit(22) 

rrr_mod_nc1=sys.argv[1]
rrr_spl_csv=sys.argv[2]
rrr_mod_nc2=sys.argv[3]


#*******************************************************************************
#Print input information
#*******************************************************************************
print('Command line inputs')
print('- '+rrr_mod_nc1)
print('- '+rrr_spl_csv)
print('- '+rrr_mod_nc2)


#*******************************************************************************
#Check if files exist 
#*******************************************************************************
try:
     with open(rrr_mod_nc1) as file:
          pass
except IOError as e:
     print('ERROR - Unable to open '+rrr_mod_nc1)
     raise SystemExit(22) 

try:
     with open(rrr_spl_csv) as file:
          pass
except IOError as e:
     print('ERROR - Unable to open '+rrr_spl_csv)
     raise SystemExit(22) 


#*******************************************************************************
#Open rrr_mod_nc1
#*******************************************************************************
print('Open rrr_mod_nc1')

f1=netCDF4.Dataset(rrr_mod_nc1,'r')

if 'COMID' in f1.dimensions:
     YV_rivid='COMID'
elif 'rivid' in f1.dimensions:
     YV_rivid='rivid'
else:
     print('ERROR - Neither COMID nor rivid exist in '+rrr_mod_nc1)
     raise SystemExit(22) 

IS_riv_tot1=len(f1.dimensions[YV_rivid])
print('- The number of river reaches in model outputs is: '+str(IS_riv_tot1))

IV_riv_tot_id1=f1.variables[YV_rivid][:]

if 'Time' in f1.dimensions:
     YV_time='Time'
elif 'time' in f1.dimensions:
     YV_time='time'
else:
     print('ERROR - Neither Time nor time exist in '+rrr_mod_nc1)
     raise SystemExit(22) 

IS_time1=len(f1.dimensions[YV_time])
print('- The number of time steps in model outputs is: '+str(IS_time1))

if 'Qout' in f1.variables:
     YV_var='Qout'
elif 'V' in f1.variables:
     YV_var='V'
else:
     print('ERROR - Neither Qout nor V exist in '+rrr_mod_nc1)
     raise SystemExit(22) 

ZV_time1=[0]*IS_time1
if YV_time in f1.variables:
     print('- The values of the time variable are obtained from metadata')
     ZV_time1=f1.variables[YV_time][:]
     ZS_TauR=f1.variables[YV_time][1]-f1.variables[YV_time][0]
else:
     print('- The values of the time variable are built from hardcoded data')
     obj_str_date=datetime.datetime.strptime(iso_str_date,'%Y-%m-%dT%H:%M:%S')
     ZV_time1[0]=calendar.timegm(obj_str_date.timetuple())
     for JS_time1 in range(1,IS_time1):
          ZV_time1[JS_time1]=ZV_time1[JS_time1-1]+ZS_TauR


#*******************************************************************************
#Open rrr_spl_csv
#*******************************************************************************
print('Open rrr_spl_csv')

IV_riv_tot_id2=[]
IV_spl_cnt=[]
IM_spl_tim=[]
with open(rrr_spl_csv) as csv_file:
     reader=csv.reader(csv_file,dialect='excel',quoting=csv.QUOTE_NONNUMERIC)
     for row in reader:
          if len(row[2:])==int(row[1]):
               IV_riv_tot_id2.append(int(row[0]))
               IV_spl_cnt.append(int(row[1]))
               IM_spl_tim.append(row[2:])
          else:
               print('ERROR - This file is inconsistent: '+rrr_spl_csv)
               raise SystemExit(22) 

IS_riv_tot2=len(IV_riv_tot_id2)
IS_spl_max=max(IV_spl_cnt)
IS_spl_tot=sum(IV_spl_cnt)
print('- The number of river reaches in subsample file is: '+str(IS_riv_tot2))
print('- The maximum number of subsamples per river reach is: '+str(IS_spl_max))
print('- The total number of subsample/river reach pairs is: '+str(IS_spl_tot))


#*******************************************************************************
#Creating hash table
#*******************************************************************************
print('Creating hash table')

IM_hsh={}
for JS_riv_tot1 in range(IS_riv_tot1):
     IM_hsh[IV_riv_tot_id1[JS_riv_tot1]]=JS_riv_tot1


#*******************************************************************************
#Generating rrr_mod_nc2 based on rrr_mod_nc1 and rrr_spl_csv
#*******************************************************************************
print('Generating rrr_mod_nc2 based on rrr_mod_nc1 and rrr_spl_csv')

#-------------------------------------------------------------------------------
#Create netCDF file
#-------------------------------------------------------------------------------
print('- Create netCDF file')
f2 = netCDF4.Dataset(rrr_mod_nc2, "w", format="NETCDF3_CLASSIC")

ZS_fill=float(1e20)

time = f2.createDimension(YV_time, None)
rivid = f2.createDimension(YV_rivid, IS_riv_tot2)

rivid = f2.createVariable(YV_rivid,"i4",(YV_rivid,))
var = f2.createVariable(YV_var,"f4",(YV_time,YV_rivid,),fill_value=ZS_fill)
if YV_time in f1.variables:
     time = f2.createVariable(YV_time,"f4",(YV_time,))

#-------------------------------------------------------------------------------
#Initialize netCDF file
#-------------------------------------------------------------------------------
print('- Initialize netCDF file')
rivid[:]=IV_riv_tot_id2
#Populate the river IDs of the subsampled file in the subsampled netCDF file

if YV_time in f1.variables:
     ZV_time2=ZV_time1
     time[:]=ZV_time2
#Populate the times of the original netCDF file in the subsampled netCDF file

IS_time2=IS_time1
for JS_time2 in range(IS_time2):
     var[JS_time2,:]=[ZS_fill]*IS_riv_tot2
#Initialize all variable values (Qout or V) that are being subsampled to NoData

#-------------------------------------------------------------------------------
#Populate netCDF file
#-------------------------------------------------------------------------------
print('- Populate netCDF file')
for JS_riv_tot2 in range(IS_riv_tot2):
     for JS_spl_cnt in range(IV_spl_cnt[JS_riv_tot2]):
          #Every river ID/mean time pair from rrr_spl_csv is accessed here.

          #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
          #Find spatial index
          #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
          IS_riv_id=IV_riv_tot_id2[JS_riv_tot2]
          JS_riv_tot1=IM_hsh[IS_riv_id]

          #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
          #Find temporal index over each possible subsample cycle
          #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
          ZS_spl_tim=IM_spl_tim[JS_riv_tot2][JS_spl_cnt]
          while ZS_spl_tim<ZV_time1[IS_time1-1]+ZS_TauR:

               JS_time2=numpy.searchsorted(ZV_time1,ZS_spl_tim)-1
               #The index of the time value closest to mean time is now known
               var[JS_time2,JS_riv_tot2]=                                      \
                                      f1.variables[YV_var][JS_time2,JS_riv_tot1]
               #Extract the value for the netCDF file
               ZS_spl_tim=ZS_spl_tim+1802700
               #Update to the next cycle


#*******************************************************************************
#Close all netCDF files
#*******************************************************************************
print('Close all netCDF files')

f1.close()
#Not sure if that does anything
f2.close()
#Closing the new netCDF file allows populating all data 


#*******************************************************************************
#End
#*******************************************************************************
