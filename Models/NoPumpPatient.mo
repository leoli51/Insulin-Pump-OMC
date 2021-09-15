model NoPumpPatient
// Patient model (based on "Roberto Visentin, Claudio Cobelli, Chiara Dalla Man. The Padova Type 2 Diabetes Simulator from Triple-Tracer Single Meal Studies: In Silico Trials also possible in Rare but Not-So-Rare Individuals. Diabetes Technology and Therapeutics, 2020")

InputReal eating;          
InputReal meal_dose;
OutputReal glucose;   

Real glucose_integral;
Real glucose_mean;

//Patient data (default values)
parameter Integer Sex = 1;                        // [0-1] 0=F, 1=M
parameter Real Age    = 55;                       // [50-62]
parameter Real Height = 172;                      // [163-175]
parameter Real BW     = 96;                       // [83-104]
parameter Real BMI    = (BW / ((Height/100)^2));  // [28.25-37.14]

parameter Real k1   = 0.066 ; 
parameter Real k2   = 0.043 ; 
parameter Real Ke1  = 0.0005;
parameter Real Ke2  = 339   ;
parameter Real Fsnc = 1     ;
parameter Real Vg   = 1     ; 
parameter Real Vmx  = 0.034 ; 
parameter Real Gb   = 127   ; 
parameter Real Km0  = 466.2 ; 
parameter Real Vi   = 0.041 ; 
parameter Real m1   = 0.314 ; 
parameter Real m2   = 0.268 ; 
parameter Real m4   = 0.443 ; 
parameter Real m5   = 0.26  ; 
parameter Real m6   = 0.017 ; 
parameter Real Kmax = 0.0426; 
parameter Real Kmin = 0.0076; 
parameter Real Kabs = 0.0542; 
parameter Real Ki   = 0.0075; 
parameter Real Kp2  = 0.0008; 
parameter Real Kp3  = 0.006 ; 
parameter Real Kp4  = 0.0484; 
parameter Real b    = 0.73 ; 
parameter Real d    = 0.1014; 
parameter Real Fcns = 1     ; 
parameter Real p2u  = 0.058 ; 
parameter Real r1   = 0.7419; 
parameter Real r2   = 0.0807; 
parameter Real f    = 0.9   ;
parameter Real ag   = 0.005 ;
parameter Real EGPb = 1.59  ;
parameter Real Ib   = 54    ;
parameter Real alpha_delay = 0.034;
parameter Real phi_s = 20.30;
parameter Real phi_d = 286.0;
parameter Real h    = 98.7  ;
parameter Real Gth  = 50;
parameter Real Gthb = 50;

Real Gpb = Gb * Vg;
Real Gtb = if (Gpb <= Ke2) then ((Fsnc - EGPb + k1 * Gpb) / k2) else ((Fsnc - EGPb + Ke1 * (Gpb - Ke2)) / Vg + k1 * Gpb) / k2;
Real Vm0 = if (Gpb <= Ke2) then ((EGPb - Fsnc)*(Km0 + Gtb) / Gtb) else ((EGPb - Fsnc - Ke1 * (Gpb-Ke2)) * (Km0+Gtb) / Gtb);
Real m30 = HEb * m1 / (1-HEb);
Real Kp1 = EGPb + Kp2*Gpb + Kp3*Ib + Kp4*Ilb;
Real Ilb = (Ipb * m2 + SRb) / (m1+m30);
Real Ipb = Ib * Vi;
Real Ievb = Ipb * m5 / m6;
Real HEb = max((SRb - m4*Ipb) / (SRb + m2*Ipb), 0);
Real CPb = 200;
Real BSA = 0.007194*(Height^(0.725))*(BW^(0.425));
Real Vc = if (Sex == 1) then (1.92*BSA+0.64) else (1.11*BSA+2.04);
Real a1  = if (BMI<=27) then 0.14 else 0.152;
Real b1  = log(2)/(0.14*Age+29.16);
Real FRA = if (BMI<=27) then 0.76 else 0.78;
Real k12 = FRA*b1+(1-FRA)*a1;
Real k01 = (a1*b1)/k12;
Real SRb = CPb/(BW*Vc*k01);
Real k21 = a1+b1-k12-k01;
Real a0g = HEb - (-ag*Gb);

Real Gp; Real Gt;
Real m3;
Real RA_meal; Real Qsto; Real Qsto1(start=0, fixed=true); Real Qsto2(start=0, fixed=true); Real Qgut(start=0, fixed=true);
Real E; Real EGP;
Real XL;
OutputReal I; Real Il; Real Ip;  Real Iev;  Real Idash;
Real HE;
Real Uii; Real Uid;
Real X(start=0, fixed=true); Real risk;
Real CP1; Real CP2;
Real ISR; Real ISRs(start=0, fixed=true); Real ISRd; Real ISRb;


//////////////////////////////////////////////////////////////////////////////
initial equation
Gp = Gpb;
Gt = Gtb;
Il = Ilb;
Ip = Ipb;
Iev = Ievb;
XL = Ib;
Idash = Ib;
CP1 = CPb;
CP2 = (k21 / k12)*CPb;


//////////////////////////////////////////////////////////////////////////////
equation

//Glucose kinetics (A1)
der(Gp) = EGP + RA_meal - Uii - E - (k1*Gp) + (k2*Gt);
der(Gt) = -Uid + (k1*Gp) - (k2*Gt) ;
glucose = Gp/Vg;

//Insulin kinetics (A2-A3-A4)
der(Il)  = -(m1 + m3)*Il + (m2*Ip + ISR/BW);
der(Ip)  = -(m2 + m4 + m5)*Ip + m1*Il + m6*Iev;
der(Iev) = -m6*Iev + m5*Ip;
I = Ip/Vi;

m3 = (HE * m1) / (1 - HE);
HE = (-ag * glucose + a0g);

//Rate of appearance (A5-A6-A7-A8)
Qsto = Qsto1 + Qsto2;
der(Qsto1) = -Kmax*Qsto1 + eating * meal_dose;
der(Qsto2) = -Kempt(b, d, Kmax, Kmin, meal_dose, Qsto)*Qsto2 + Kmax*Qsto1;
der(Qgut) =  -Kabs*Qgut + Kempt(b, d, Kmax, Kmin, meal_dose, Qsto)*Qsto2;
RA_meal = (f * Kabs * Qgut) / BW;


//Endogenous glucose production (A9-A10-A11)
EGP = Kp1 - Kp2*Gp - Kp3*XL - Kp4*Il;
der(XL) = (-Ki) * (XL - Idash);
der(Idash) = (-Ki) * (Idash - I);


//Glucose utilization, insulin independent (A12)
Uii = Fcns;

//Glucose utilization, insulin dependent (A13-A14-A15-A16)
Uid = ((Vm0 + (Vmx * X * (1 + (r1 * risk))))* Gt) / (Km0 + Gt);
der(X) = (-p2u)*X + p2u*(I - Ib);

risk =
  if (glucose >= Gb) then
    0
  elseif (glucose >= Gth and glucose <= Gb) then
    10 * (F(glucose, Gb, r2))^2
  else
    10 * (F(Gth, Gthb, r2))^2;


//Renal excretion (A17)
E =
  if (Gp > Ke2) then
    Ke1 * (Gp - Ke2)
  else
    0;

//C-peptide Kinetics (A18-A19-A20-A21-A22)
der(CP1) = (-(k01 + k21))*CP1 + k12*CP2 + (ISR/Vc);
der(CP2) = (-k12 * CP2) + (k21 * CP1);

ISRb = CPb * k01 * Vc;
ISR = ISRs + ISRd + ISRb;
der(ISRs) = -alpha_delay * (ISRs - Vc * phi_s * (glucose - h));
ISRd = if (der(glucose) >= 0) then Vc * phi_d * der(glucose) else 0;

der(glucose_integral) = glucose;

algorithm
glucose_mean := if (time == 0) then 0 else glucose_integral / time;

end NoPumpPatient;

