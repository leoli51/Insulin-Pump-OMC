block FMonitor
// Monitors the glucose levels in the patient and computes the time the glucose levels are out of bounds: 
// glucose levels should never be below 50 mg/dL or above 200 mg/dL

InputReal glucose;          // glucose in body
parameter Real T=0.1;
parameter Real target=100;  // glucose target value
parameter Real range=15;    // acceptable divergence from target value
Real timeOutOfOptimalRange; 
Real outOfRangeWeighted;

Boolean glucoseOutOfBounds; 
Boolean glucoseCritical;


initial equation
glucoseOutOfBounds = false; 
glucoseCritical = false;

equation
glucoseOutOfBounds = glucose<50 or glucose>200;

algorithm
//computes the time out of the optimal glucose value range
when sample(0,T) then
    if glucose > (target+range) or glucose < (target-range) then
        timeOutOfOptimalRange:= pre(timeOutOfOptimalRange) + T;
        outOfRangeWeighted:= pre(outOfRangeWeighted) + T * abs((glucose - target) / target);
    end if;
end when;


// set glucose critical if glucose is out of bounds
when edge(glucoseOutOfBounds) then
    glucoseCritical := true;
end when;


end FMonitor;
