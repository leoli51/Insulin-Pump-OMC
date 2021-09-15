block MealGenerator

OutputReal eating;
OutputReal meal_dose;                     


parameter Real dose = 400;  // dose of meal
parameter Real meal_length = 60;  // lenght of meal (minutes)
parameter Real meals_per_day = 4;  // periodic meals: every 8 hours.
Real meal_period = 1440 / meals_per_day;
Boolean meal_on, meal_off;

initial equation
meal_on = false;
meal_off = false;

equation

meal_dose = dose;

// periodic meal of duration meal_length every meal_period minutes

when sample(0, meal_period/2) then
meal_on = not(pre(meal_on));
end when;

when sample(meal_length, meal_period/2) then
meal_off = not(pre(meal_off));
end when;

when edge(meal_on) then
    eating = 1;
elsewhen edge(meal_off) then
    eating = 0;
end when;


end MealGenerator;