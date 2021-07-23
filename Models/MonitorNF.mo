block MonitorNF
//misura il rapporto tra l'insulina rilasciata dalla pompa e quella nel corpo del paziente
parameter Real T=0.1;
InputReal insulinPump;//insulina dalla pompa
InputReal insulinBody;//insulina nel corpo
Real insulinRatio;


algorithm
when sample(0,T) then
insulinRatio:=pre(insulinRatio)+insulinPump/insulinBody;
end when;


end MonitorNF;
