block Pump
//modello della pompa di insulina

InputReal glucose;    //quantita' di glucosio del paziente
OutputReal insulinOutput;   //quantita' di insulina da dare al paziente

//Pump parameters
parameter Real T = 10; //sampling time della pompa(ogni 10 minuti)
parameter Real targetmin = 90; //lower bound del range di glucosio target
parameter Real targetmax = 110; //upper bound del range di glucosio target
parameter Real mindose = 1;
parameter Real corr = 6.2;
parameter Real change = 1;

Real pre;//valore di glucosio all'ultimo sample time
Real prepre;//valore di glucosio all'penultimo sample time
Real insulin;

initial equation
insulin = 0;
pre = glucose;
prepre = glucose;


algorithm

when sample(0, T) then
//Glucosio Basso
if (glucose < targetmin) then
  insulin := 0;

//Glucosio Alto
elseif (glucose > targetmax) then
  //In aumento
  if (glucose > pre) then
    insulin := max(((glucose - pre) / change), mindose);
  //In discesa
  elseif (glucose < pre) then
    if ( (glucose - pre) <= (pre - prepre) ) then
      insulin := 0;
    else
      insulin := mindose;
    end if;
  //Stabile
  else
    insulin := mindose;
  end if;

//Glucosio accettabile
else
  //In dimunuzione o stabile
  if (glucose <= pre) then
    insulin := 0;
  //In aumento, ma con velocita' in diminuzione
  elseif (glucose > pre and (glucose - pre) < (pre - prepre) ) then
    insulin := 0;
  //In aumento, e con velocita' in aumento
  else
    if (((glucose - pre) / change) > mindose) then
      insulin := ((glucose - pre) / change);
    else 
      insulin := mindose;
    end if;
  end if;
end if;

prepre := pre;
pre := glucose;
insulinOutput := insulin*corr;
end when;
end Pump;
