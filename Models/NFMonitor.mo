block NFMonitor

parameter Real T=0.1;

InputReal insulinPump; // insulin released by the pump
InputReal insulinBody; // insulin released by the body
Real insulinRatio;
Real insulinInjected;
Real totalInsulin;

initial equation
insulinInjected = 0;
totalInsulin = 0;

equation
der(insulinInjected) = insulinPump;
der(totalInsulin) = insulinPump + insulinBody;


algorithm
when sample(0,T) then
    insulinRatio := pre(insulinRatio) + insulinPump / insulinBody;
end when;


end NFMonitor;
