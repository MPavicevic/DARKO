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
d           Consumers         /D1, D2, D3/
s           Producers         /HeatPump, ElectricHeater, Boiler/
b           Block orders      /BO1, BO2/
t           traiding period within a single day  /t1*t3/
n           trading day       /n1, n2/;
;

Alias(d,dd);
Alias(s,ss);
Alias(bo,bobo);
Alias(t,tt);
Alias(n,nn);

*Parameters as defined in the input file
* \u indicate that the value is provided for one single unit
PARAMETERS
QuantityDemand(d,t)              [MW]      demand of the consumer d in time period t in cases
PriceDemand(d,t)                 [€\MW]    price of the consumer d in time period t in cases
QuantitySupply(s,t)              [MW]      demand of the producer s in time period t in cases
PriceSupply(s,t)                 [€\MW]    price of the producer s in time period t in cases
QuantityBlockOrder(bo,t)          [MW]      demand of the producer s in time period t in cases
PriceBlockOrder(bo)               [€\MW]    price of the block order
;

*===============================================================================
*Data import
*===============================================================================

$gdxin %inputfilename%

$Load d
$Load s
$Load bo
$Load t
$Load n
$Load QuantityDemand
$Load PriceDemand
$Load QuantitySupply
$Load PriceSupply
$Load QuantityBlockOrder
$Load PriceBlockOrder
;

Display
d,
s,
bo,
t,
n,
QuantityDemand,
PriceDemand,
QuantitySupply,
PriceSupply,
QuantityBlockOrder,
PriceBlockOrder,
;

*===============================================================================
*Definition of variables
*===============================================================================
POSITIVE VARIABLES
x(d,t)    acceptance ratio on consumer side
y(s,t)    acceptance ratio on supplier side
z(bo)     acceptance ratio on block orders
;

BINARY VARIABLE
z1(bo)    binary variable
;

FREE VARIABLE
wtot      total welfate
;

*===============================================================================
*Definition of lower and upper bounds
*===============================================================================
x.up(d,t) = 1;
y.up(s,t) = 1;
z.up(bo) = 1;

*===============================================================================
*Declaration and definition of equations
*===============================================================================
EQUATIONS
EQ_Welfare      define objective function
EQ_Power     define power balance
EQ_Blockorder_lb   define lower bound on block order
EQ_Blockorder_ub   define uper bound on block order;

* Objective function
EQ_Welfare ..
         wtot
         =E=
         sum((d,t), x(d,t)*QuantityDemand(d,t)*PriceDemand(d,t)) - sum((s,t), y(s,t)*QuantitySupply(s,t)*PriceSupply(s,t))-sum((bo,t), z(bo)*QuantityBlockOrder(bo,t)*PriceBlockOrder(bo));
*Power balance
EQ_Power(t) ..
         sum(d, x(d,t)*QuantityDemand(d,t))
         =E=
          sum(s, y(s,t)*QuantitySupply(s,t)) + sum(b, z(bo)*QuantityBlockOrder(bo,t));
*Lower bound on block order
EQ_Blockorder_lb(bo) ..
         0.5*z1(bo)
         =L=
         z(bo);
*Upper bound on block order
EQ_Blockorder_ub(bo) ..
         z(bo)
         =L=
         z1(bo);

*===============================================================================
*Definition of models
*===============================================================================
MODEL DARKO  /
EQ_Welfare
EQ_Power
EQ_Blockorder_lb
EQ_Blockorder_ub/;

*===============================================================================
*Solving the models
*===============================================================================
SOLVE DARKO using MIP MAXIMIZE wtot;

*===============================================================================
*Result export
*===============================================================================
PARAMETER
QuantityDemand(d,t)
PriceDemand(d,t)
QuantitySupply(s,t)
PriceSupply(s,t)
QuantityBlockOrder(bo,t)
PriceBlockOrder(bo)
;

QuantityDemand(d,t) = Q_Demand.L(d,t);
PriceDemand(d,t) = P_Demand.L(d,t);
QuantitySupply(s,t) = Q_Supply.L(s,t);
PriceSupply(s,t) = P_Supply.L(s,t);
QuantityBlockOrder(bo,t) = Q_BlockOrder.L(bo,t);
PriceBlockOrder(bo) = P_BlockOrder.L(bo,t);

