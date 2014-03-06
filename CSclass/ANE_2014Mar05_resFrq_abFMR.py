import os
import visa
import time
import datetime
import numpy as np

import equipFunc as eqfunc

#import zhinst.ziPython as zipy
#import zhinst.utils as ziut
#from pylab import plot, show, title, xlabel, ylabel, subplot

import matplotlib.pyplot as plt
plt.ion()   #Need to have this to continuously update plot

import pylab    #Need to change name of figure window

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-fn", help="file number [default=0]",
                    type=int, default = 0)
parser.add_argument("-avg", help="data avg [default=10]",
                    type=int, default = 10)
parser.add_argument("-isrc", help="DC source current [uA] [no input = NONE]",
                    type=float)
parser.add_argument("-ht40pwr", help="ht40 power [dBm] [default=0]",
                    type=int, default = 0)
parser.add_argument("-setH", help="set field to measure resonance",
                    type=int, default = 200)
parser.add_argument("-Hmod", help="field modulation current [default=0]",
                    type=float, default = 0.0)
parser.add_argument("-frqStart", help="Freq. sweep start [GHz] [default=2]",
                    type=float, default = 2.0)
parser.add_argument("-frqEnd", help="Freq. sweep end [GHz] [default=5]",
                    type=float, default = 5.0)
parser.add_argument("-frqStep", help="Freq. sweep step [GHz] [default=0.002]",
                    type=float, default = 0.002)
args = parser.parse_args()

#################
''' Constants '''

freqStart = args.frqStart       # Start Frquency
freqEnd = args.frqEnd           # End Frequency
delFreq = args.frqStep          # Change in Frequency
ht40pwr = args.ht40pwr          # Power [dBm[
waitMW = 0.5                    # wait time after each config of ht40 [sec]

minH = 0
maxH = 4000         # maximum voltage sent to Kepco:: FullRange = 12000 = 12.0 volt
setH = args.setH    # set voltage/field to do measurments
delH = 100          # delta voltage
waitH = 0.1         # unit: sec

dataAvg = args.avg  # No. averaging at each field
waitData = 0.0      # wait for next data to read
fieldTrack = 0      # tracks the last field measurement: used for zeroing the field at the end of program

filename = '2014Mar04_'+str(args.fn)+'_abFMR_H('+str(setH)+')_idc('+str(args.isrc)+'uA)_pwr('+str(args.ht40pwr)+'dBm)'

''' END: Constants '''

##### Data file header #####
''' File Header '''
def filehead(f,filename):
    f.write("Inductive-FMR: "+filename+".dat"+"\n")
    f.write("+++++++Info: Header (13th line), data (14th line)++++++++\n")
    f.write("Start: "+startTime+"\n")
    f.write("\n")    
    f.write("--------Setting--------\n")
    f.write("Bias:: isrc("+str(args.isrc)+") [None=NO keithley]:: Sample live(Shorted)\n")
    f.write("Modulation:: field by Lock-in["+oscFrq+", "+oscAmp+" ("+str(args.Hmod)+" Arms)]\n")    
    f.write("Lock-in:: SEN("+str(lockSEN)+"), TC("+tc+"), phase("+refphase+"), ACgain("+acgain+"), Slope("+slope+"), offset(off)\n")
    f.write("Microwave:: ht40pwr("+str(args.ht40pwr)+"dBm)\n")
    f.write("Field:: setH("+str(setH)+"), Field wait("+str(waitH)+" sec), maxH("+str(maxH)+")\n")
    f.write("Data:: dataAvg("+str(dataAvg)+"), waitData("+str(waitData)+")\n")
    f.write("+++++++++++++++++++++++\n")
    f.write("index Field f(GHz) lock_x_avg lock_y_avg lock_ph_avg\n")   
##### Data file header #####

##### This is the main program #####
def main():
    global startTime, endTime, fieldTrack
    connectEquip()
    
    '''Get data'''
    print '\n'
    print '--------------- FMR: Initization! ---------------'
    startTime = str(time.asctime( time.localtime(time.time()) ))
    print 'Localtime: ' + startTime
    print 'Data Avg = ',str(dataAvg), '\n'

    f = open(filename + '.dat', 'w')
    filehead(f,filename)     #with def. above, this writes the header section.

    plotInit(filename)  #initiate plot
    x_axis = list()
    y1_axis = list()
    y2_axis = list()
    y3_axis = list()

    ### Adjusting External Magnetic Field "Start" ###
    print '=============== FMR: Measurement Start! ==============='
    print '... Initization: changing the field ...'
    eqfunc.sr7225_daq1(sr7225, 0.0, waitH)  #Set the field to zero

    for i in np.arange(minH, maxH+delH, delH): # positive current
        fieldTrack = i
        eqfunc.sr7225_daq1(sr7225, i, waitH)

    for i in np.arange(maxH, setH-delH, -delH):
        fieldTrack = i
        eqfunc.sr7225_daq1(sr7225, i, waitH)
    ### Adjusting External Magnetic Field "End" ###

    print 'ht40  : f = ', freqStart, ' GHz ', eqfunc.setF(ht40,freqStart)
    time.sleep(waitMW)
    print 'ht40  : pwr = ', ht40pwr, ' GHz ', eqfunc.setP(ht40,ht40pwr)
    time.sleep(waitMW)
    print '...mw ON..........', eqfunc.outputON(ht40) 
    time.sleep(waitMW)

    index = 0           # index no. to keep the how many measurements are made
    for freq in np.arange(freqStart, freqEnd+delFreq, delFreq):        
        index += 1    
        print '\n_______chaging frquency_______'
        print 'ht40  : f = ', freq, ' GHz ', eqfunc.setF(ht40,freq)
        time.sleep(waitMW)

        Xval1 = 0.0
        Yval1 = 0.0
        Phval1 = 0.0
            
        for count in range(0, dataAvg):    
            read1X = float(sr7225.ask('X'))/10000.0*lockSEN
            read1Y = float(sr7225.ask('Y'))/10000.0*lockSEN
            read1Ph = float(sr7225.ask('PHA'))/18000.0*180.0
                
            #print freq,'/',freqEnd,'GHz ===',count,'=== ',read1X, '   ',read1Y,'  ',read1Ph
            Xval1 += read1X
            Yval1 += read1Y
            Phval1 += read1Ph

        Xval1 = Xval1/dataAvg
        Yval1 = Yval1/dataAvg
        Phval1 = Phval1/dataAvg
        print 'avg_lock_X = ',Xval1,'   avg_lock_Y = ', Yval1,'   avg_lock_Ph = ', Phval1
        print >> f, index, fieldTrack, freq, Xval1, Yval1, Phval1
        
        x_axis.append(freq)
        y1_axis.append(Xval1)
        y2_axis.append(Yval1)
        y3_axis.append(Phval1)
        plotCurv(x_axis,y1_axis,y2_axis, y3_axis, str('r.-'))

    f.close()
    endTime = str(time.asctime( time.localtime(time.time()) ))

    ### Insert endTime at 4th line of file
    endTimeInsert(filename, endTime, 4)

    ### Do end of measure routine
    endMeasure()

    #this line prevents the plot to close automatically
    #raw_input()

##### End: main #####

##### End of measure routine #####
def endMeasure():
    ''' End of Measurement: 1. Returning ht40 '''
    print '\n'
    print '========= End of Measurement: Returning ht40... ========='
    print 'ht40 output is off: ... ', eqfunc.outputOFF(ht40)
    print 'ht40  : f = ', freqStart, ' GHz ', eqfunc.setF(ht40,freqStart)
    
    ''' End of Measurement: 2. Removing Field '''
    print '===== End of Measurement: Removing Magnetic Field... ====='

    del_sign = (minH - fieldTrack)/abs(minH - fieldTrack)
    for i in np.arange(fieldTrack, minH+delH, delH*del_sign):
        print 'Field now = ',i
        eqfunc.sr7225_daq1(sr7225, i, waitH)
           
    print '..field removed...\n'

    endTime = str(time.asctime( time.localtime(time.time()) ))
    print 'Start time: ', startTime
    print 'End   time: ', endTime

##### Insert endTime in the data file ######
def endTimeInsert(filename, endTime, nthLine):
    f = open(filename + '.dat', 'r')
    data = f.readlines()
    f.close()
    data[nthLine-1:nthLine] = [
    'End:   '+endTime+'\n']
    f = open(filename+'.dat', 'w')
    f.writelines(data)
    f.close()

##### Connecting equipments #####
def connectEquip():
    ##################################''' CONNECT TO EQUIPMENT '''
    os.system('cls')
    global sr7225, kly, ht40
    global lockSEN, refphase, acgain, slope, tc, ie, oscAmp, oscFrq

    print '=============== Connecting to Equipments ==============='
    print 'Instruments found: ',visa.get_instruments_list(),'\n' # Check all equip. connections

    sr7225 = visa.instrument('GPIB0::13') #SR7225 Lock-In
    print sr7225,('...is... \n'),sr7225.ask('ID')
    lockSEN = float(sr7225.ask('SEN.'))
    refphase = str(sr7225.ask('refp.'))
    acgain = str( int(sr7225.ask('ACGAIN'))*10 )+'dB'
    slope = str(( int(sr7225.ask('slope'))+1 )*6)+ 'dB/oct'
    tc = str(sr7225.ask('tc.'))
    ie = str(sr7225.ask('ie'))
    oscAmp = str(sr7225.ask('oa.'))+' Vrms'
    oscFrq = str(sr7225.ask('of.'))+' Hz'

    #kly = visa.instrument('GPIB0::24') #Keithley 2400 Soucemeter
    #print kly,('...is... \n'),kly.ask('*IDN?')

    ht40 = visa.instrument('GPIB0::30') #Hittite40
    print ht40,('...is... \n'),ht40.ask('*IDN?')
    #ht20.write('*RST')
    #print '\n__________\nFollowing device has been reset\nht20 on GPIB0::40 is ... ', ht20, '\nIts identity is ...',ht20.ask('*IDN?'),'\nSystem error? ...', ht20.ask(':system:error?'),'\n__________\n'


##### Plotting #####
def plotCurv(x_axis,y1_axis, y2_axis, y3_axis,color):        
    p1.plot(x_axis, y1_axis, color)
    p2.plot(x_axis, y2_axis, color)
    p3.plot(x_axis, y3_axis, color)    
    #plt.pause(0.000001)
    plt.draw()

def plotInit(filename):
    global p1, p2, p3

    #below two lines changes the name of window title
    fig = pylab.gcf()
    fig.canvas.set_window_title(filename)

    p1=plt.subplot(3, 1, 1)
    p2=plt.subplot(3, 1, 2)
    p3=plt.subplot(3, 1, 3)

    p1.set_title("Inductive-FMR:"+startTime)
    dataRange = abs(freqEnd - freqStart)
    p1.set_xlim([freqStart-dataRange/20 , freqEnd+dataRange/20])
    p2.set_xlim([freqStart-dataRange/20 , freqEnd+dataRange/20])
    p3.set_xlim([freqStart-dataRange/20 , freqEnd+dataRange/20])

    p1.set_ylabel('X')
    p2.set_ylabel('Y')
    p3.set_ylabel('Ph')
    p3.set_xlabel('f(GHz)')   

    print '\n=== Ignore above warning: adjust plot position ==='
    print '======== Measurement will start in 5 sec =========\n'
    #plt.pause(7)
    return p1, p2, p3
    
##### END: plotting #####    

if __name__ == '__main__':
    main()
    




