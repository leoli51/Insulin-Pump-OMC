# This script tries to determine the optimal value for the insulin_multiplier parameter.
# That is the amount of insulin to inject that maximizes the key performance indicator:
# 1 / (interest * time_glucose_out_of_optimal_range / total_time + (1 - interest) * injected_insulin / total_insulin + 1)
# The KPI is defined as above since we want to reduce the injected insulin and the time out of the 
# optimal range. the interest parameter is used to weight the influence of these values in the 
# KPI. The so defined KPI is easy to work with since it is limited in the range [0, 1].
import time
import json
import random
import glob
import os
from OMPython import OMCSessionZMQ


# Parameters
interest = 0.8

def compute_kpi(time_out_of_bounds, total_time, injected_insulin, total_insulin, interest):
        return 1 / (interest * time_out_of_bounds / total_time + (1 - interest) * injected_insulin / total_time + 1)

# start OMC session
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

stopTime=1440.0 
omc.sendExpression("buildModel(System, stopTime="+str(stopTime)+",method='rungekutta')")
omc.sendExpression("getErrorString()")
start=time.time()

# load patient data ranges
with open('PatientDataRanges.json') as f:
        patient_data_ranges = json.load(f)


def find_best_kpi(start, stop, step, test_per_value=100):
        best_kpi = -1
        best_value = -1
        test_value = start
        tests_done = 0
        while test_value < stop:
                kpis = []
                print "Starting tests for insulin_multiplier=%f" % test_value
                for i in range(test_per_value):
                        with open ("modelica_rand.in", 'wt') as f:
                                parameter_string= ""
                                #generate random patient parameters
                                for p_name, p_values in patient_data_ranges.items():
                                        val = None
                                        if p_name == "Sex":
                                                val = random.choice(p_values)
                                        else:
                                                val = random.uniform(p_values[0], p_values[1])
                                        parameter_string +="patient."+p_name+"="+str(val)+"\n"
                                parameter_string += "pump.insulin_multiplier="+str(test_value)

                                f.write(parameter_string)

                        # run simulation
                        os.system("./System -overrideFile=modelica_rand.in -s=rungekutta")

                        # check if there was some critical error .. in case continue
                        glucose_critical = omc.sendExpression("val(fm.glucoseCritical, "+str(stopTime)+", \"System_res.mat\")")

                        if type(glucose_critical) != float:
                                continue
                        if glucose_critical != 0.0:
                                print "critical value of glucose for insulin_multiplier=%f" % test_value
                                print "Skipping dangerous value!"
                                kpis.clear()
                                break
                        
                        # retrieve kpi parameters  
                        injected_insulin = omc.sendExpression("val(nfm.insulinInjected, "+str(stopTime)+", \"System_res.mat\")")
                        total_insulin = omc.sendExpression("val(nfm.totalInsulin, "+str(stopTime)+", \"System_res.mat\")")
                        time_out_of_bounds = omc.sendExpression("val(fm.timeOutOfOptimalRange, "+str(stopTime)+", \"System_res.mat\")")
                        
                        if type(injected_insulin) != float or type(total_insulin) != float or type(time_out_of_bounds) != float:
                                continue

                        # compute kpi
                        kpi = compute_kpi(time_out_of_bounds, stopTime, injected_insulin, total_insulin, interest)
                        kpis.append(kpi)
                        tests_done += 1
                
                if len(kpis) > 0:
                        average_kpi = sum(kpis) / len(kpis)
                        if average_kpi > best_kpi:
                                best_kpi = average_kpi
                                best_value = test_value
                
                test_value += step

        return best_kpi, best_value, tests_done 

best_kpi = 0
insulin_multiplier_min = 0.1
insulin_multiplier_max = 10
insulin_multiplier_steps = [1, .5, .1]
best_insulin_multiplier = insulin_multiplier_min
test_per_value = 100
test_num = 0

for insulin_multiplier_step in insulin_multiplier_steps:
        print "Finding best insulin multiplier in range [%f ; %f] with step %f" % (insulin_multiplier_min, insulin_multiplier_max, insulin_multiplier_step)
        best_kpi, best_insulin_multiplier, tests_done = find_best_kpi(insulin_multiplier_min, insulin_multiplier_max, insulin_multiplier_step, test_per_value)                
        insulin_multiplier_min = max(0.1, best_insulin_multiplier - insulin_multiplier_step)
        insulin_multiplier_max = min(10, best_insulin_multiplier + insulin_multiplier_step + 0.1)
        test_num += tests_done
     
# compute total time
totTime=time.time()-start

print "Total tests %d" % test_num
print "Best KPI = %s" % best_kpi
print "Best Insulin Multiplier = %s" % best_insulin_multiplier
print "Total time = %f" % totTime
