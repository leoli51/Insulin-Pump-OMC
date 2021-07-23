class System

Patient patient;
Pump pump;
MealGenerator mgn;
MonitorF mF;
MonitorNF mNF;

equation
connect(pump.insulinOutput, patient.insulinInput);
connect(pump.glucose, patient.glucose);
connect(mgn.meal, patient.meal);
connect(mF.glucose, patient.glucose);
connect(pump.insulinOutput, mNF.insulinPump);
connect(patient.I, mNF.insulinBody);
connect(patient.I, mF.insulinBody);

end System;
