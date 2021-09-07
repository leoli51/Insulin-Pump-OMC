class System

Patient patient;
Pump pump;
MealGenerator mgn;
MonitorF mF;
MonitorNF mNF;

NoPumpPatient no_pump_patient;

equation
connect(pump.insulinOutput, patient.insulinInput);
connect(pump.glucose, patient.glucose);
connect(mgn.eating, patient.eating);
connect(mF.glucose, patient.glucose);
connect(pump.insulinOutput, mNF.insulinPump);
connect(patient.I, mNF.insulinBody);
connect(patient.I, mF.insulinBody);

connect(mgn.eating, no_pump_patient.eating);

end System;
