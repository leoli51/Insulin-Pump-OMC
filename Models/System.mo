class System

Patient patient;
Pump pump;
MealGenerator mgn;
FMonitor fm;
NFMonitor nfm;

NoPumpPatient no_pump_patient;

equation
connect(pump.insulinOutput, patient.insulinInput);
connect(pump.glucose, patient.glucose);
connect(mgn.eating, patient.eating);
connect(mgn.meal_dose, patient.meal_dose);
connect(fm.glucose, patient.glucose);
connect(pump.insulinOutput, nfm.insulinPump);
connect(patient.I, nfm.insulinBody);

connect(mgn.eating, no_pump_patient.eating);
connect(mgn.meal_dose, no_pump_patient.meal_dose);

end System;
