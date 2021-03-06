import os
import sys
import math
import time
import json
import random
import glob
from OMPython import OMCSessionZMQ


def compute_mean(samples):
        return sum(samples) / len(samples)

def compute_ct(samples, t, mean, delta, rv_range):
        #t = len(samples)
        # first: 
        #       compute standard deviation based on the samples we collected
        #       note: for efficiency we compute the mean before     
        standard_deviation = 0
        for sample in samples:
                standard_deviation += (sample - mean)**2
        standard_deviation /= t
        standard_deviation = standard_deviation ** 0.5

        # second: 
        #        compute dt:
        #        dt must satisfy the property: sum(dt, t=1, t=infinity) <= delta
        #        therefore we use the 1/2^t sequence multiplied by delta
        #        since 1/2^t converges to 1 multiplied by delta it converges to delta
        dt = delta / (2**(len(samples)/10))

        # third:
        #        compute ct
        ct = standard_deviation * (2 * math.log(3 / dt) / t)**0.5 + 3 * rv_range * math.log(3 / dt) / t

        return ct


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

samples_per_step = 10   # number of samples for each step
delta = .2              # delta , given in input                       
error = .1              # error, given in input 
rv_range = 150          # glucose range value...

lower_bound = 0
upper_bound = 1<<32

test_num = 0

tests_failed = 0

verify_log_string = ""
verify_output_string = ""

while (1 + error) * lower_bound < (1 - error) * upper_bound:
        # run samples_per_step simulations, for each simulation generate a new set of parameters
        # use ebstop algorithm to determine when to stop
        samples = []

        i = 0
        while i < samples_per_step:
                print "Test "+str(test_num)
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

                        f.write(parameter_string)

                verify_log_string += "\nTest "+str(test_num)+":\n"

                # run simulation
                os.system("./System -overrideFile=modelica_rand.in -s=rungekutta  >> %s" % VERIFY_LOG_FILE)

                # check if glucose levels crossed the critical threshold
                glucose_critical = omc.sendExpression("val(fm.glucoseCritical, "+str(stopTime)+", \"System_res.mat\")")
                if type(glucose_critical) != float:
                        continue
                
                # collect glucose mean sample
                glucose_mean = omc.sendExpression("val(patient.glucose_mean, "+str(stopTime)+", \"System_res.mat\")")
                samples.append(glucose_mean)

                test_num += 1
                i += 1

                #tempo fuori dal range ottimale di glucosio
                time_out_of_bounds = omc.sendExpression("val(fm.timeOutOfOptimalRange, "+str(stopTime)+", \"System_res.mat\")")

                verify_output_string += "Test "+str(test_num)
                if glucose_critical:
                        verify_output_string += " Critical glucose levels detected\n\n"
                        tests_failed += 1   
                else:
                        verify_output_string += " No error detected\n\n"   
                        

        # Empirical Bernstein Stopping algorithm to see if we should continue sampling
        if len(samples) == 0:
                continue
        
        mean_rv_t = compute_mean(samples)
        ct = compute_ct(samples, test_num, mean_rv_t, delta, rv_range)

        lower_bound = max(lower_bound, mean_rv_t - ct)
        upper_bound = min(upper_bound, mean_rv_t + ct)

        print "Mean RV: %f ct: %f LB: %f UB: %f" % (mean_rv_t, ct, lower_bound, upper_bound)

print "Executed: %d tests. Desired accuracy reached!" % test_num
total_time=time.time()-start

with open (VERIFY_LOG_FILE, 'w') as f:
        f.write(verify_log_string)
with open (VERIFY_OUTPUT_FILE, 'w') as f:
        f.write(verify_output_string)

print "\n%d Tests failed and %d Tests passed out of %d Tests" % (tests_failed, test_num-tests_failed, test_num)
print "Total time: %f" % total_time 
