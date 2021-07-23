function F
//Funzione f(G), come richiesta da formule A15-A16 dal documento del paziente.

InputReal G;
InputReal Gb;
InputReal r2;
OutputReal y;

algorithm
y := (log(G))^r2 - (log(Gb)^r2);

end F;
