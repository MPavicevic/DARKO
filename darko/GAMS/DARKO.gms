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
u           Units Supply Side
d           ProsumersConsumers Demand Side
o           Order type
n           Nodes
l           Lines
t           Technologies
tr(t)       Renewable technologies
f           Fuel types
s(u)        Storage Technologies
h           Hours
i(h)        Subset of simulated hours for one iteration
z(h)        Subset of all simulated hours
sk          Sectors
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

PARAMETERS
Config
AccaptanceBlockOrdersMin(u)              [%]      Accaptance ratio for block orders
AvailabilityFactorDemandOrder(d,h)       [%]      Share of maximum demand in time period h
AvailabilityFactorSimpleOrder(u,h)       [%]      Share of maximum Simple order in time period h
AvailabilityFactorBlockOrder(u,h)        [%]      Share of maximum Block order in time period h
AvailabilityFactorFlexibleOrder(u)       [%]      Accaptance ratio for block orders
MaxDemand(d)                             [MW\u]   Maximum demand
Fuel(u,f)                                [n.a.]   Fuel type              {1 0}
LocationDemandSide(d,n)                  [n.a.]   Location               {1 0}
LocationSupplySide(u,n)                  [n.a.]   Location               {1 0}
OrderType(u,o)                           [n.a.]   Order type             {1 0}
PowerCapacity(u)                         [MW\u]   Installed capacity
PriceDemandOrder(d,h)                    [€\MW]   Price ofer of the consumer d in time period h
PriceSimpleOrder(u,h)                    [€\MW]   Price ofer of the simple order u in time period h
PriceBlockOrder(u)                       [€\MW]   Default block order price
PriceFlexibleOrder(u)                    [€\MW]   Default block order price
Sector(d,sk)                             [n.a.]   Demand sector type     {1 0}
Technology(u,t)                          [n.a.]   Technology type        {1 0}
LineNode(l,n)                            [n.a.]   Incidence matrix       {-1 +1}
FlowMaximum(l,h)                         [MW]     Line limits
FlowMinimum(l,h)                         [MW]     Minimum flow

* Scalar variables necessary to the loop:
scalar FirstHour,LastHour,LastKeptHour,day,ndays,failed;
FirstHour = 1;

*===============================================================================
*Data import
*===============================================================================

$gdxin %inputfilename%

$LOAD u
$LOAD d
$LOAD o
$LOAD n
$LOAD l
$LOAD t
$LOAD tr
$LOAD f
$LOAD s
$LOAD h
$LOAD z
$LOAD sk
$LOAD AccaptanceBlockOrdersMin
$LOAD AvailabilityFactorDemandOrder
$LOAD AvailabilityFactorSimpleOrder
$LOAD AvailabilityFactorBlockOrder
$LOAD AvailabilityFactorFlexibleOrder
$LOAD Config
$LOAD MaxDemand
$LOAD Fuel
$LOAD LocationDemandSide
$LOAD LocationSupplySide
$LOAD OrderType
$LOAD PowerCapacity
$LOAD PriceDemandOrder
$LOAD PriceSimpleOrder
$LOAD PriceBlockOrder
$LOAD PriceFlexibleOrder
$LOAD Sector
$LOAD Technology
$LOAD LineNode
$LOAD FlowMinimum
$LOAD FlowMaximum
;

Display
u,
d,
o,
n,
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
Config,
MaxDemand,
Fuel,
LocationDemandSide,
LocationSupplySide,
OrderType,
PowerCapacity,
PriceDemandOrder,
PriceSimpleOrder,
PriceBlockOrder,
PriceFlexibleOrder,
Sector,
Technology,
LineNode,
FlowMaximum,
FlowMinimum
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
EQ_Flow_limits_lower define lower limit on flows between zones
;

* Objective function
EQ_Welfare ..
         TotalWelfare
         =E=
         sum((d,h), AcceptanceRatioOfDemandOrders(d,h)*AvailabilityFactorDemandOrder(d,h)*MaxDemand(d)*PriceDemandOrder(d,h))
         - sum((u,h), AcceptanceRatioOfSimpleOrders(u,h)*AvailabilityFactorSimpleOrder(u,h)*PowerCapacity(u)*PriceSimpleOrder(u,h))
         - sum((u,h), AcceptanceRatioOfBlockOrders(u)*AvailabilityFactorBlockOrder(u,h)*PowerCapacity(u)*PriceBlockOrder(u))
         - sum((u,h), ClearingStatusOfFlexibleOrder(u,h)*AvailabilityFactorFlexibleOrder(u)*PowerCapacity(u)*PriceFlexibleOrder(u));
*Power balance
EQ_PowerBalance(h,n,o,t,sk) ..
         sum(d, AcceptanceRatioOfDemandOrders(d,h)*AvailabilityFactorDemandOrder(d,h)*MaxDemand(d)*LocationDemandSide(d,n))
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
EQ_Flow_limits_lower(l,h)..
         FlowMinimum(l,h)
         =L=
         Flow(l,h)
;
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
EQ_Flow_limits_upper
EQ_Flow_limits_lower/;

*===============================================================================
*Solving the models
*===============================================================================
SOLVE DARKO using MIP MAXIMIZE TotalWelfare;

*===============================================================================
*Result export
*===============================================================================
PARAMETER
OutputAcceptanceRatioOfDemandOrders(d,h)
OutputAcceptanceRatioOfSimpleOrders(u,h)
OutputAcceptanceRatioOfBlockOrders(u)
OutputClearingStatusOfBlockOrder(u)
OutputClearingStatusOfFlexibleOrder(u,h)
OutputFlow(l,h)
OutputMarginalPrice(h,n,o,t,sk)
OutputTotalWelfare
;

OutputAcceptanceRatioOfDemandOrders(d,h) = AcceptanceRatioOfDemandOrders.L(d,h);
OutputAcceptanceRatioOfSimpleOrders(u,h) = AcceptanceRatioOfSimpleOrders.L(u,h);
OutputAcceptanceRatioOfBlockOrders(u) = AcceptanceRatioOfBlockOrders.L(u);
OutputClearingStatusOfBlockOrder(u) = ClearingStatusOfBlockOrder.L(u);
OutputClearingStatusOfFlexibleOrder(u,h) = ClearingStatusOfFlexibleOrder.L(u,h);
OutputFlow(l,h) = Flow.L(l,h);
OutputMarginalPrice(h,n,o,t,sk) = EQ_PowerBalance.m(h,n,o,t,sk);
OutputTotalWelfare = TotalWelfare.L;

EXECUTE_UNLOAD "Results.gdx"
OutputAcceptanceRatioOfDemandOrders,
OutputAcceptanceRatioOfSimpleOrders,
OutputAcceptanceRatioOfBlockOrders,
OutputClearingStatusOfBlockOrder,
OutputClearingStatusOfFlexibleOrder,
OutputFlow,
OutputMarginalPrice,
OutputTotalWelfare
*status
;

display
AcceptanceRatioOfDemandOrders.L,
AcceptanceRatioOfSimpleOrders.L,
AcceptanceRatioOfBlockOrders.L,
ClearingStatusOfBlockOrder.L,
ClearingStatusOfFlexibleOrder.L,
Flow.L,
EQ_PowerBalance.m,
TotalWelfare.L
