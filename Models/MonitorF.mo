block MonitorF
// Monitors the glucose and insulin levels in the patient and computes the time the glucose levels are out of bounds: 
// glucose levels should never be below 50 mg/dL or above 200 mg/dL
// insulin levels should never be below 0 mg/dL

InputReal glucose;          // glucose in body
InputReal insulinBody;      // insulin in body
parameter Real T=0.1;
parameter Real target=100;  //target glucosio
parameter Real range=15;    //range accettabile rispetto al target
Real timeOutOfOptimalRange; //tempo fuori dal range ottimale del glucosio
Boolean glucoseOutOfBounds; //true se il glucosio <50 o>200
Boolean glucoseCritical;
Boolean insulinOutOfBounds;
Boolean insulinCritical;


initial equation
//glucoseOutOfBounds = false; 
insulinOutOfBounds = false;  
glucoseCritical = false;
insulinCritical = false;

equation
glucoseOutOfBounds = glucose<50 or glucose>200;
insulinOutOfBounds = insulinBody<0;

algorithm
//computes the time out of the optimal glucose value range
when sample(0,T) then
    if glucose > (target+range) or glucose < (target-range) then
        timeOutOfOptimalRange:=pre(timeOutOfOptimalRange)+(T*(abs(target-glucose)/100));
    end if;
end when;

//controllo glucosio<50
when edge(glucoseOutOfBounds) then
    glucoseCritical := true;
end when;

//controllo insulina<0
when edge(insulinOutOfBounds) then
    insulinCritical := true;
end when;

end MonitorF;
