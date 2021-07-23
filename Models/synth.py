#script per ricercare il corr, ovvero il valore da moltiplicare alla quantita' di insulina
#da rilasciare, che meglio minimizza un kpi cosi' definito:
#0.6*<percentuale di tempo in cui il glucosio si trova fuori dal range ottimale> + (1 - 0.6)*(1 + insulina rilasciata dalla pompa/insulina totale nel corpo)
import os
import sys
import math
import time
import json
import random
import glob

from OMPython import OMCSessionZMQ

# start OMC session
omc = OMCSessionZMQ()
omc.sendExpression("getVersion()")
omc.sendExpression("cd()")
omc.sendExpression("loadModel(Modelica)")
omc.sendExpression("getErrorString()")

o# load all .mo files in current directory
mo_files = glob.glob("*.mo")
for mo_file in mo_files:
        omc.sendExpression("loadFile(\"%s\")" % mo_file)
        omc.sendExpression("getErrorString()")

stopTime=1440.0#un giorno
omc.sendExpression("buildModel(System, stopTime="+str(stopTime)+",method='rungekutta')")
omc.sendExpression("getErrorString()")
start=time.time()

#file di log
with open ("log", 'wt') as f:
        f.write("###LOGS###"+"\n")
        f.flush()
        os.fsync(f)
#file con risultati
with open ("output.txt", 'wt') as f:
        f.write("Outcomes"+"\n\n")
        f.flush()
        os.fsync(f)
#file json con i possibili parametri del paziente
with open('patientData.json') as f:
        patientData = json.load(f)
        f.close()

N = 100    # numero di of samples
bestKPI=999999999999 #KPI da minimizzare
bestCorr=-1
for corr in range(1, 11, 1):
#for corr in [5.2,5.4,5.6,5.8,6.2,6.4,6.6,6.8]:#se 5 e 6 erano gia' stati testati con 1000 samples
#for corr in [5,5.2,5.4,5.6,5.8,6,6.2,6.4,6.6,6.8]:#se 5 e 6 non erano gia' stati testati con 1000 samples
        num_fail = 0 #controlla se ci sono fallimenti con il corr attuale
        w = 0.0 #controlla se il glucosio scende sotto la soglia dell'ipoglicemia o sopra la soglia dell'iperglicemia
        print " "
        print "corr = ", corr
        sumKPI=0
        for i in range(N):
                print corr,i
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
                                        g.flush()
                                        os.fsync(g)
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
            os.fsync(g)
        #se il KPI appena calcolato e' piu' basso dell'attuale migliore
        if ((sumKPI/N < bestKPI) and num_fail==0):
                bestCorr = corr
                bestKPI = sumKPI/N

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
