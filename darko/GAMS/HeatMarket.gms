$Title DARKO model

$eolcom //
Option threads=8;
Option IterLim=1000000000;
Option ResLim = 10000000000;

option
    limrow = 0,     // equations listed per block
    limcol = 0,     // variables listed per block
    solprint = off,     // solver's solution output printed
    sysout = off;       // solver's system output printed

*===============================================================================
*Definition of the dataset-related options
*===============================================================================

* Print results to excel files (0 for no, 1 for yes)
$set Verbose 0

* Set debug mode. !! This breaks the loop and requires a debug.gdx file !!
* (0 for no, 1 for yes)
$set Debug 0

* Print results to excel files (0 for no, 1 for yes)
$set PrintResults 0

* Name of the input file (Ideally, stick to the default Input.gdx)
$set InputFileName Inputs.gdx

* Flag to retrieve status or not
* (1 to retrieve 0 to not)
$setglobal RetrieveStatus 0

*===============================================================================
*Definition of sets and parameters
*===============================================================================
SETS
u           Units Supply Side                    /HOBO_GAS, HOBO_BIO, THMS_OTH/
d           ProsumersConsumers Demand Side       /D1, D2, D3/
o           Order type                           /Simple, Block, Flexible/
n           Nodes                                /Z1, Z2/
l           Lines                                /Z1Z2, Z2Z1/
t           Technologies                         /HOBO, SOTH, THMS/
tr(t)       Renewable technologies               /SOTH/
f           Fuel types                           /GAS, BIO, OTH/
s(t)        Storage Technologies                 /THMS/
h           Hours                                /h1*h3/
i(h)        Subset of simulated hours for one iteration
z(h)        Subset of all simulated hours
sk          Sectors                              /REZ, IND/
;

Alias(d,dd);
Alias(n,nn);
Alias(l,ll);
Alias(u,uu);
Alias(t,tt);
Alias(f,ff);
Alias(s,ss);
Alias(h,hh);
Alias(i,ii);
Alias(o,oo);
Alias(sk,sksk);

$ontext
*Parameters as defined in the input file
* \u indicate that the value is provided for one single unit
PARAMETERS
$offtext
Parameter AccaptanceBlockOrdersMin(u)         [%]      Accaptance ratio for block orders
/HOBO_BIO    0.5
,HOBO_GAS    0/;
TABLE AvailabilityFactorDemandOrder(d,h)       [%]      Share of maximum demand in time period h
        h1   h2   h3
D1     0.5  0.6  0.7
D2     0.9  0.8  0.7
D3     1    1    1;
TABLE AvailabilityFactorSimpleOrder(u,h)       [%]      Share of maximum Simple order in time period h
              h1   h2   h3
HOBO_BIO      0     0    0
HOBO_GAS      1     1    1;
TABLE AvailabilityFactorBlockOrder(u,h)        [%]      Share of maximum Block order in time period h
              h1   h2   h3
HOBO_BIO      1     1    1
HOBO_GAS      0     0    0;
Parameter AvailabilityFactorFlexibleOrder(u)         [%]      Accaptance ratio for block orders
/THMS_OTH   1/;
*Config
Parameter Demand(d)                                [MW\u]   Maximum demand
/D1 50
,D2 100
,D3 30/;
TABLE Fuel(u,f)                                [n.a.]   Fuel type {1 0}
              GAS   BIO  OTH
HOBO_BIO      0      1    0
HOBO_GAS      1      0    0
THMS_OTH      0      0    1;
TABLE LocationDemandSide(d,n)                  [n.a.]   Location {1 0}
     Z1 Z2
D1   1  0
D2   1  0
D3   0  1;
TABLE LocationSupplySide(u,n)                  [n.a.]   Location {1 0}
          Z1   Z2
HOBO_BIO   1   0
HOBO_GAS   1   0
THMS_OTH   0   1;
TABLE Order(u,o)                               [n.a.]   Order type {1 0}
          Simple  Block  Flexible
HOBO_BIO   0        1       0
HOBO_GAS   1        0       0
THMS_OTH   0        0       1;
Parameter PowerCapacity(u)                         [MW\u]   Installed capacity
/HOBO_BIO 50
,HOBO_GAS 100
,THMS_OTH 30/;
TABLE PriceDemandOrder(d,h)                    [€\MW]   Price ofer of the consumer d in time period h
        h1   h2   h3
D1      20   20   20
D2      30   30   30
D3      30   30   30;
TABLE PriceSimpleOrder(u,h)                    [€\MW]   Price ofer of the simple order u in time period h
          h1   h2  h3
HOBO_BIO  0    0   0
HOBO_GAS  25   25  25;
Parameter PriceBlockOrder(u)                       [€\MW]   Default block order price
/HOBO_BIO 10
,HOBO_GAS 0/;
Parameter PriceFlexibleOrder(u)                       [€\MW]   Default block order price
/THMS_OTH 30/;
TABLE Sector(d,sk)                             [n.a.]   Demand sector type {1 0}
       REZ  IND
D1     1    0
D2     0    1
D3     0    1;
TABLE Technology(u,t)                          [n.a.]   Technology type {1 0}
          HOBO
HOBO_BIO  1
HOBO_GAS  1;
Table LineNode(l,n)                    [n.a.]   Incidence matrix {-1 +1}
       Z1    Z2
Z1Z2   1     -1
Z2Z1   -1    1;
Table FlowMaximum(l,h)                 [MW]     Line limits
       h1   h2  h3
Z1Z2   20   30  20
Z2Z1   30   20  30;
*FlowMinimum(l,h)                 [MW]     Minimum flow

Display
u,
d,
o,
l,
t,
tr,
f,
s,
h,
*z,
sk,
AccaptanceBlockOrdersMin,
AvailabilityFactorDemandOrder,
AvailabilityFactorSimpleOrder,
AvailabilityFactorBlockOrder
AvailabilityFactorFlexibleOrder,
*Config,
Demand,
Fuel,
LocationDemandSide,
LocationSupplySide,
Order,
PowerCapacity,
PriceDemandOrder,
PriceSimpleOrder,
PriceBlockOrder,
PriceFlexibleOrder,
Sector,
Technology,
LineNode,
FlowMaximum
;

*===============================================================================
*Definition of variables
*===============================================================================
POSITIVE VARIABLES
AcceptanceRatioOfDemandOrders(d,h)    acceptance ratio of demand orders
AcceptanceRatioOfSimpleOrders(u,h)    acceptance ratio of simple orders
AcceptanceRatioOfBlockOrders(u)      acceptance ratio of block orders
Flow(l,h) [MW]    Flow through lines
;

BINARY VARIABLE
ClearingStatusOfBlockOrder(u)    binary variable
ClearingStatusOfFlexibleOrder(u,h) binary variable
;

FREE VARIABLE
TotalWelfare      total welfate  
;

*===============================================================================
*Definition of lower and upper bounds
*===============================================================================
AcceptanceRatioOfDemandOrders.up(d,h) = 1;
AcceptanceRatioOfSimpleOrders.up(u,h) = 1;
AcceptanceRatioOfBlockOrders.up(u) = 1;

*===============================================================================
*Declaration and definition of equations
*===============================================================================
EQUATIONS
EQ_Welfare         define objective function
EQ_PowerBalance    define power balance
EQ_Blockorder_lb   define lower bound on block order
EQ_Blockorder_ub   define uper bound on block order
EQ_Flexibleorder   define flexible order constraints
EQ_Flow_limits_upper define upper limit on flows between zones
;

* Objective function
EQ_Welfare ..
         TotalWelfare
         =E=
         sum((d,h), AcceptanceRatioOfDemandOrders(d,h)*AvailabilityFactorDemandOrder(d,h)*Demand(d)*PriceDemandOrder(d,h))
         - sum((u,h), AcceptanceRatioOfSimpleOrders(u,h)*AvailabilityFactorSimpleOrder(u,h)*PowerCapacity(u)*PriceSimpleOrder(u,h))
         - sum((u,h), AcceptanceRatioOfBlockOrders(u)*AvailabilityFactorBlockOrder(u,h)*PowerCapacity(u)*PriceBlockOrder(u))
         - sum((u,h), ClearingStatusOfFlexibleOrder(u,h)*AvailabilityFactorFlexibleOrder(u)*PowerCapacity(u)*PriceBlockOrder(u));
*Power balance
EQ_PowerBalance(h,n,o,t,sk) ..
         sum(d, AcceptanceRatioOfDemandOrders(d,h)*AvailabilityFactorDemandOrder(d,h)*Demand(d)*LocationDemandSide(d,n))
         =E=
         sum(u, AcceptanceRatioOfSimpleOrders(u,h)*AvailabilityFactorSimpleOrder(u,h)*PowerCapacity(u)*LocationSupplySide(u,n))
         + sum(u, AcceptanceRatioOfBlockOrders(u)*AvailabilityFactorBlockOrder(u,h)*PowerCapacity(u)*LocationSupplySide(u,n))
         + sum(u, ClearingStatusOfFlexibleOrder(u,h)*AvailabilityFactorFlexibleOrder(u)*PowerCapacity(u)*LocationSupplySide(u,n))
         + sum(l,Flow(l,h)*LineNode(l,n));
*Lower bound on block order
EQ_Blockorder_lb(u) ..
         AccaptanceBlockOrdersMin(u)*ClearingStatusOfBlockOrder(u)
         =L=
         AcceptanceRatioOfBlockOrders(u);
*Upper bound on block order
EQ_Blockorder_ub(u) ..
         AcceptanceRatioOfBlockOrders(u)
         =L=
         ClearingStatusOfBlockOrder(u);
*Flexible order
EQ_Flexibleorder(u) ..
         sum(h, ClearingStatusOfFlexibleOrder(u,h))
         =L=
         1;
*Flows are above minimum values
*EQ_Flow_limits_lower(l,h)..
*         FlowMinimum(l,h)
*         =L=
*         Flow(l,h)
*;
*Flows are below maximum values
EQ_Flow_limits_upper(l,h)..
         Flow(l,h)
         =L=
         FlowMaximum(l,h)
;

*===============================================================================
*Definition of models
*===============================================================================
MODEL DARKO  /
EQ_Welfare
EQ_PowerBalance
EQ_Blockorder_lb
EQ_Blockorder_ub
EQ_Flexibleorder
EQ_Flow_limits_upper/;

*===============================================================================
*Solving the models
*===============================================================================
SOLVE DARKO using MIP MAXIMIZE TotalWelfare;

*===============================================================================
*Result export
*===============================================================================
$ontext
PARAMETER
QuantityDemand(d,i)
PriceDemand(d,i)
QuantitySupply(s,i)
PriceSupply(s,i)
QuantityBlockOrder(bo,i)
PriceBlockOrder(bo)
;

QuantityDemand(d,i) = Q_Demand.L(d,i);
PriceDemand(d,i) = P_Demand.L(d,i);
QuantitySupply(s,i) = Q_Supply.L(s,i);
PriceSupply(s,i) = P_Supply.L(s,i);
QuantityBlockOrder(bo,i) = Q_BlockOrder.L(bo,i);
PriceBlockOrder(bo) = P_BlockOrder.L(bo,t);
$offtext

display
AcceptanceRatioOfDemandOrders.L,
AcceptanceRatioOfSimpleOrders.L,
AcceptanceRatioOfBlockOrders.L,
ClearingStatusOfBlockOrder.L,
ClearingStatusOfFlexibleOrder.L,
Flow.L,
EQ_PowerBalance.m
TotalWelfare.L


