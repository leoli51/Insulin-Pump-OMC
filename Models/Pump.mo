// Insulin Pump model
block Pump

InputReal glucose;          // glucose level of patient
OutputReal insulinOutput;   // insulin output

//Pump parameters
parameter Real T = 10;          // sampling time of the pump (10 minutes)
parameter Real targetmin = 90;  // lower bound of target glucose range
parameter Real targetmax = 110; // upper bound of target glucose range
parameter Real mindose = 1;
parameter Real corr = 8;//6.2;
parameter Real change = 1;      

Real prev;       // glucose value at time - 1
Real prevprev;   // glucose value at time - 2
Real insulin;

initial equation
insulin = 0;
prev = glucose;
prevprev = glucose;


algorithm

when sample(0, T) then
// glucose level: low
if (glucose < targetmin) then
  insulin := 0;

// glucose level: high
elseif (glucose > targetmax) then
  // raising
  if (glucose > prev) then
    insulin := max(((glucose - prev) / change), mindose);
  // dropping
  elseif (glucose < prev) then
    if ( (prev - glucose) >= (prevprev - prev) ) then
      insulin := 0;
    else
      insulin := mindose;
    end if;
  // stable
  else
    insulin := mindose;
  end if;

// glucose level: acceptable
else
  // dropping
  if (glucose <= prev) then
    insulin := 0;
  // raising (negative order 2 derivative)
  elseif (glucose > prev and (glucose - prev) - (prev - prevprev) < 0) then
    insulin := 0;
  // raising (positive order 2 derivative)
  else
    if (((glucose - prev) / change) > mindose) then
      insulin := ((glucose - prev) / change);
    else 
      insulin := mindose;
    end if;
  end if;
end if;

prevprev := prev;
prev := glucose;
insulinOutput := insulin*corr;
end when;
end Pump;
