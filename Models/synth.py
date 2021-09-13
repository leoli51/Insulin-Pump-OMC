# This script tries to determine the optimal value for the insulin_multiplier parameter.
# That is the amount of insulin to inject that maximizes the key performance indicator:
# 1 / (interest * time_glucose_out_of_optimal_range / total_time + (1 - interest) * injected_insulin / total_insulin + 1)
# The KPI is defined as above since we want to reduce the injected insulin and the time out of the 
# optimal range. the interest parameter is used to weight the influence of these values in the 
# KPI. The so defined KPI is easy to work with since it is limited in the range [0, 1].
import math
import time
import json
import random
import glob

from OMPython import OMCSessionZMQ


# Parameters
interest = 0.8

def compute_kpi(time_out_of_bounds, total_time, injected_insulin, total_insulin, interest):
        return 1 / (interest * time_out_of_bounds / total_time + (1 - interest) * injected_insulin / total_time + 1)

SYNTH_LOG_FILE = "synth.log"
SYNTH_OUTPUT_FILE = "synth.output"

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

# log file
with open (SYNTH_LOG_FILE, 'wt') as f:
        f.write("### LOGS ###\n")

# output file
with open (SYNTH_OUTPUT_FILE, 'wt') as f:
        f.write("### TEST RESULTS ###\n")

# load patient data ranges
with open('PatientDataRanges.json') as f:
        patient_data_ranges = json.load(f)


def find_best_kpi(start, stop, step, test_per_value=100):
        best_kpi = 0
        best_value = 0
        for test_value in range(start, stop, step):
                kpis = []
                for i in range(test_per_value):
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

                        # run simulation
                        os.system("./System -overrideFile=modelica_rand.in -s=rungekutta  >> %s" % SYNTH_LOG_FILE)

                        # check if there was some critical error .. in case continue
                        glucose_critical = bool(omc.sendExpression("val(mF.glucoseCritical, "+str(stopTime)+", \"System_res.mat\")"))
                        insulin_critical = bool(omc.sendExpression("val(mF.insulinCritical, "+str(stopTime)+", \"System_res.mat\")"))

                        if glucose_critical or insulin_critical:
                                continue
                                #handle this
                        
                        # retrieve kpi parameters  
                        injected_insulin = omc.sendExpression("val(nfm.insulinInjected, "+str(stopTime)+", \"System_res.mat\")")
                        total_insulin = omc.sendExpression("val(nfm.totalInsulin, "+str(stopTime)+", \"System_res.mat\")")
                        time_out_of_bounds = omc.sendExpression("val(fm.timeOutOfOptimalRange, "+str(stopTime)+", \"System_res.mat\")")
                        
                        # compute kpi
                        kpi = compute_kpi(time_out_of_bounds, stopTime, injected_insulin, total_insulin, interest)
                        kpis.append(kpi)
                
                if len(kpis) > 0:
                        average_kpi = sum(kpis) / len(kpis)
                        if average_kpi > best_kpi:
                                best_kpi = average_kpi
                                best_value = test_value

        return best_kpi, best_value 

best_KPI = 0

insulin_multiplier_min = 0.1
insulin_multiplier_max = 10
insulin_multiplier_step = 0.5
best_insulin_multiplier = insulin_multiplier_min

for insulin_multiplier in range(insulin_multiplier_min, insulin_multiplier_max, insulin_multiplier_step):
    
        sumKPI=0
                with open ("modelica_rand.in", 'wt') as f:
                        #trovo valori random per alcuni parametri del paziente
                        stringa="pum.corr="+str(corr)+"\n"
                        for par in patientData.keys():
                                if par=="Sex":
                                    val=str(random.choice([0,1]))
                                else:
                                    val=math.trunc(np.random.uniform(patientData[par][0],patientData[par][1])*10000.0)/10000.0
                                stringa+="pat."+str(par)+"="+str(val)+"\n"
                        #trovo valori random per i seed cosi' da variare le mc
                        stringa+="pat.mc.localSeed="+str(random.randint(1000,999999))
                        stringa+="\npat.mc.globalSeed="+str(random.randint(1000,999999))
                        stringa+="\nmgn.mc2.localSeed="+str(random.randint(1000,999999))
                        stringa+="\nmgn.mc2.globalSeed="+str(random.randint(1000,999999))+"\n"
                        f.write(stringa)
                        f.flush()
                        os.fsync(f)
                #eseguo la simulazione
                os.system("./System -overrideFile=modelica_rand.in -s=rungekutta >> log")
                #mi permette di vedere il valore del monitor del glucosio alla fine della simulazione
                w = omc.sendExpression("val(mF.w, "+str(stopTime)+", \"System_res.mat\")")
                z = omc.sendExpression("val(mF.z, "+str(stopTime)+", \"System_res.mat\")")
                #controllo il valore dell'insulina dalla pompa e tot nel corpo a fine operazione
                rapIns=omc.sendExpression("val(mNF.rapIns, "+str(stopTime)+", \"System_res.mat\")")
                #controllo il tempo fuori dal range del glucosio
                timeOutBounds=omc.sendExpression("val(mF.T_outofBounds, "+str(stopTime)+", \"System_res.mat\")")
                try:
                        #se l'insulina e' scesa sotto 0 o il glucosio sotto 50
                        if (z >= 0.5) or (w >= 0.5):
                                if (z >= 0.5):
                                    print "ERRORE: valore di insulina critico."
                                if (w >= 0.5):
                                    print "ERRORE: valore di glucosio critico."
                                num_fail += 1.0
                                with open ("output.txt", 'a') as g:
                                        g.write("Correzione = "+str(corr)+", Test:"+str(i)+".\nFAIL con parametri:\n"+stringa+"\n")
                                break
                except TypeError:
                        num_fail+=1
                        print "TypeError"
                        break
                #myKPI = 0.6*<percentuale di tempo fuori range per il glucosio> + (1 - 0.6)*(1 + insulin-dalla-pompa/insulina-body)
                myKPI=0.6*(timeOutBounds*100/(stopTime))+(1 - 0.6)*(1 + rapIns/stopTime)
                sumKPI+=myKPI
                print "_______________"
        #se non ci sono stati problemi, calcola la media
        if (num_fail==0):
            avgKPI=sumKPI/N
        #se ci sono stati problemi, non calcola la media
        else:
            avgKPI="OPS, si e' verificato un problema! Uno o piu' requisiti del sistema paziente sono stati violati."
        print "avg KPI=", avgKPI
        #salva il risultato nel file di output
        with open ("output.txt", 'a') as g:
            g.write("Correzione = "+str(corr)+", KPI:"+str(avgKPI)+"\n")
            g.flush()
            os.fsync(g
#calcola il tempo totale di CPU
totTime=time.time()-start

#salva il risultato nel file di output
with open ("output.txt", 'a') as g:
        g.write("\n\n--------\n"+
        "Best KPI = "+str(bestKPI)+",\nBest Corr ="+str(bestCorr)+
        "\nTempo Totale ="+str(totTime))
        g.flush()
        os.fsync(g)
print " "
print "Best KPI = ", bestKPI
print "Best Corr = ", bestCorr
print "Tempo Totale =", totTime
