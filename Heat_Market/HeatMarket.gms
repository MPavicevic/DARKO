Sets
     d Consumers         /D1, D2, D3/
     s Producers         /HeatPump, ElectricHeater, Boiler/
     b Block orders      /BO1, BO2/
     t traiding period within a single day  /t1*t3/
     n trading day       /n1, n2/;

Table
     QuantityDemand(d,t) demand of the consumer d in time period t in cases
          t1     t2      t3
     D1  300    200     500
     D2  400    350     300
     D3  100    100     100 ;
Table
     PriceDemand(d,t) price of the consumer d in time period t in cases
          t1     t2      t3
     D1   2      2       3
     D2   1      1       3
     D3   3      3       3  ;
Table
     QuantitySupply(s,t) demand of the producer s in time period t in cases
                          t1     t2      t3
     HeatPump            200    200     200
     ElectricHeater      200    200     200
     Boiler              300    300     300 ;
Table
     PriceSupply(s,t) price of the producer s in time period t in cases
                          t1     t2      t3
     HeatPump             2      2       2
     ElectricHeater       1      1       1
     Boiler               3      3       3 ;
Table
     QuantityBO(b,t) demand of the producer s in time period t in cases
                          t1     t2      t3
     BO1                  50     50      50
     BO2                 100    100      50;

Parameter PriceBO(b) /BO1 1
                      BO2 2/;
*Table
*     PriceBO(b) price of the producer s in time period t in cases
*                          t1     t2      t3
*     BO1                  2      2       2;

Variables
     x(d,t)    acceptance ratio on consumer side
     y(s,t)    acceptance ratio on supplier side
     z(b)      acceptance ratio on block orders
     z1(b)     binary variable
     wtot      total welfate
Positive variables
x
y
z;

x.up(d,t) = 1;
y.up(s,t) = 1;
z.up(b) = 1;

Binary variable
z1;

Equations
     welfare      define objective function
     power(t)     define power balance
     blockorder_lb(b)   define lower bound on block order
     blockorder_ub(b)   define uper bound on block order;

welfare ..        wtot =e= sum((d,t), x(d,t)*QuantityDemand(d,t)*PriceDemand(d,t)) - sum((s,t), y(s,t)*QuantitySupply(s,t)*PriceSupply(s,t))-sum((b,t), z(b)*QuantityBO(b,t)*PriceBO(b));
power(t) ..       sum(d, x(d,t)*QuantityDemand(d,t)) =e= sum(s, y(s,t)*QuantitySupply(s,t)) + sum(b, z(b)*QuantityBO(b,t));
blockorder_lb(b) ..     0.5*z1(b) =l= z(b);
blockorder_ub(b) ..     z(b) =l= z1(b);

model heatmarket  /all/;

solve heatmarket using mip maximize wtot;



