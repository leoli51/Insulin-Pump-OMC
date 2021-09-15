// Function Kempt(Qsto) as described in the A5-A6-A7-A8 formulas of the T2D simulation paper
function Kempt

InputReal b;
InputReal d;
InputReal Kmax;
InputReal Kmin;
InputReal Dose;
InputReal Q;
OutputReal y;

protected Real alpha, beta;

algorithm

alpha := 5/(2*Dose*(1-b));

beta := 5/(2*Dose*d);

y := Kmin + ((Kmax - Kmin)/2)*(tanh(alpha*(Q - beta*Dose)) - tanh(beta*(Q - d*Dose)) + 2);

end Kempt;
