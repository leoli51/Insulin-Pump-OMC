#script per verificare che il sistema funzioni in tutti i casi operativi possibili.
#i test sono generati con distribuzione uniforme, dando a ogni possibile combinazione la stessa probabilita'
#di essere usata nel test.
import os
import sys
import math
import time
import json
import random
import glob
from OMPython import OMCSessionZMQ

def ebstop():
        # one may want to sample until
        # the estimated error is within some small number ǫ of
        # the true error with probability at least 1 − δ.
        

VERIFY_LOG_FILE = "verify.log"
VERIFY_OUTPUT_FILE = "verify.output"

# Start OMC session
omc = OMCSessionZMQ()
omc.sendExpression("getVersion()")
omc.sendExpression("cd()")
omc.sendExpression("loadModel(Modelica)")
omc.sendExpression("getErrorString()")

# load all .mo files in current directory
mo_files = glob.glob("*.mo")
for mo_file in mo_files:
        omc.sendExpression("loadFile(\"%s\")" % mo_file)
        omc.sendExpression("getErrorString()")

stopTime=1440.0 # minutes in a 24h day
omc.sendExpression("buildModel(System, stopTime="+str(stopTime)+",method='rungekutta')")
omc.sendExpression("getErrorString()")
start=time.time()

# log file
with open (VERIFY_LOG_FILE, 'wt') as f:
        f.write("### LOGS ###\n")

# output file
with open (VERIFY_OUTPUT_FILE, 'wt') as f:
        f.write("### TEST RESULTS ###\n")


# load patient data ranges
with open('PatientDataRanges.json') as f:
        patient_data_ranges = json.load(f)

N = 100    # numero di samples
# TODO add ebstop algorithm 

tests_failed = 0

# run N simulations, for each simulation generate a new set of parameters
for i in range(N):
        print "Test "+str(i+1)
        with open ("modelica_rand.in", 'wt') as f:
                parameter_string=""
                
                #generate random patient parameters
                for p_name, p_values in patient_data_ranges.items():
                        val = None
                        if p_name == "Sex":
                                val = random.choice(p_values)
                        else:
                                val = random.uniform(p_values[0], p_values[1])
                        
                        parameter_string +="patient."+p_name+"="+str(val)+"\n"

                #trovo valori random per i seed cosi' da variare le mc
                #parameter_string+="pat.mc.localSeed="+str(random.randint(1000,999999))
                #parameter_string+="\npat.mc.globalSeed="+str(random.randint(1000,999999))
                #parameter_string+="\nmgn.mc2.localSeed="+str(random.randint(1000,999999))
                #parameter_string+="\nmgn.mc2.globalSeed="+str(random.randint(1000,999999))+"\n"
                f.write(parameter_string)

        with open (VERIFY_LOG_FILE, 'a') as f:
                f.write("\nTest "+str(i+1)+":\n")

        # run simulation
        os.system("./System -overrideFile=modelica_rand.in -s=rungekutta  >> %s" % VERIFY_LOG_FILE)

        # mi permette di vedere il valore del monitor del glucosio alla fine della simulazione
        glucose_critical = omc.sendExpression("val(mF.glucoseCritical, "+str(stopTime)+", \"System_res.mat\")")
        insulin_critical = omc.sendExpression("val(mF.insulinCritical, "+str(stopTime)+", \"System_res.mat\")")

        #tempo fuori dal range ottimale di glucosio
        time_out_of_bounds = omc.sendExpression("val(mF.T_outofBounds, "+str(stopTime)+", \"System_res.mat\")")

        with open (VERIFY_OUTPUT_FILE, 'a') as f:
                f.write("Test "+str(i+1))

                if not (insulin_critical or glucose_critical):
                        f.write(" No error detected")
                else:
                        f.write(" Critical insulin levels detected" * insulin_critical + " Critical glucose levels detected" * glucose_critical)
                        tests_failed += 1

                f.write("_______________\n\n")


total_time=time.time()-start
print " "
if (tests_failed > 0):
    print "%d Tests failed and %d Tests passed out of %d Tests" % (tests_failed, N-tests_failed, N)
else:
    print "All tests passed, no errors detected."

print "Total time: %f" % total_time 
