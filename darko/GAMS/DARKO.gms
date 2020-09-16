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
* Configuration of the simulation environment
Config

* Availabilities
AccaptanceBlockOrdersMin(u)              [%]      Accaptance ratio for block orders
AvailabilityFactorDemandOrder(d,h)       [%]      Share of maximum demand in time period h
AvailabilityFactorSimpleOrder(u,h)       [%]      Share of maximum Simple order in time period h
AvailabilityFactorBlockOrder(u,h)        [%]      Share of maximum Block order in time period h
AvailabilityFactorFlexibleOrder(u)       [%]      Accaptance ratio for block orders

* Node data
LocationDemandSide(d,n)                  [n.a.]   Location               {1 0}
LocationSupplySide(u,n)                  [n.a.]   Location               {1 0}
NodeHourlyRampUp(n, h)                   [%\h\n]  Node ramp up limit
NodeHourlyRampDown(n, h)                 [%\h\n]  Node ramp down limit
NodeDailyRampUp(n)                       [%\24h\n] Node daily ramp up limit
NodeDailyRampDown(n)                     [%\24h\n] Node daily ramp up limit
NodeInitial(n)

* Prices
PriceDemandOrder(d,h)                    [€\MW]   Price ofer of the consumer d in time period h
PriceSimpleOrder(u,h)                    [€\MW]   Price ofer of the simple order u in time period h
PriceBlockOrder(u)                       [€\MW]   Default block order price
PriceFlexibleOrder(u)                    [€\MW]   Default block order price

* Interconection lines
LineNode(l,n)                            [n.a.]   Incidence matrix       {-1 +1}
FlowMaximum(l,h)                         [MW]     Line limits
FlowMinimum(l,h)                         [MW]     Minimum flow
LineHourlyRampUp(l, h)                   [%\h\n]  Interconection line ramp up limit
LineHourlyRampDown(l, h)                 [%\h\n]  Interconection line ramp down limit
LineDailyRampUp(l)                       [%\24h\n] Interconection daily line ramp up limit
LineDailyRampDown(l)                     [%\24h\n] Interconection daily line ramp down limit
LineInitial(l)

* Units / demands
MaxDemand(d)                             [MW\u]   Maximum demand
PowerCapacity(u)                         [MW\u]   Installed capacity
OrderType(u,o)                           [n.a.]   Order type             {1 0}
Technology(u,t)                          [n.a.]   Technology type        {1 0}
Fuel(u,f)                                [n.a.]   Fuel type              {1 0}
Sector(d,sk)                             [n.a.]   Demand sector type     {1 0}
UnitRampUp(u)                            [%\h\u]  Unit ramp up limit
UnitRampDown(u)                          [%\h\u]  Unit ramp down limit
LinkedBlockOrderIncidenceMatrix(u)
MinimumIncomeFixed(u)
MinimumIncomeVariable(u)

* Storage
StorageChargingCapacity(s)               [MW\u]   Storage capacity
StorageChargingEfficiency(s)             [%]      Charging efficiency
StorageSelfDischarge(s)                  [%\day]  Self-discharge of the storage units
StorageCapacity(s)                       [MWh\u]    Storage capacity
StorageDischargeEfficiency(s)            [%]      Discharge efficiency
StorageOutflow(s,h)                      [MWh\u]    Storage outflows
StorageInflow(s,h)                       [MWh\u]    Storage inflows (potential energy)
StorageInitial(s)                        [MWh]    Storage level before initial period
StorageProfile(s,h)                      [%]      Storage level to be resepected at the end of each horizon
StorageMinimum(s)                        [MWh]    Storage minimum
StorageFinalMin(s)               [MWh]   Minimum storage level at the end of the optimization horizon
;

* Scalar variables necessary to the loop:
SCALAR FirstHour,LastHour,LastKeptHour,day,ndays,nloops,cloop,failed;
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
$LOAD UnitRampUp
$LOAD UnitRampDown
$LOAD NodeDailyRampUp
$LOAD NodeDailyRampDown
$LOAD NodeHourlyRampUp
$LOAD NodeHourlyRampDown
$LOAD LineDailyRampUp
$LOAD LineDailyRampDown
$LOAD LineHourlyRampUp
$LOAD LineHourlyRampDown
$LOAD LineInitial
$LOAD NodeInitial
$LOAD StorageChargingCapacity
$LOAD StorageChargingEfficiency
$LOAD StorageDischargeEfficiency
$LOAD StorageSelfDischarge
$LOAD StorageCapacity
$LOAD StorageInflow
$LOAD StorageInitial
$LOAD StorageProfile
$LOAD StorageMinimum
$LOAD StorageOutflow
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
FlowMinimum,
UnitRampUp,
UnitRampDown,
NodeDailyRampUp,
NodeDailyRampDown,
NodeHourlyRampUp,
NodeHourlyRampDown,
LineDailyRampUp,
LineDailyRampDown,
LineHourlyRampUp,
LineHourlyRampDown,
LineInitial,
NodeInitial,
StorageChargingCapacity,
StorageChargingEfficiency,
StorageSelfDischarge,
StorageCapacity,
StorageInflow,
StorageInitial,
StorageProfile,
StorageMinimum,
StorageOutflow
;

*===============================================================================
*Definition of variables
*===============================================================================
POSITIVE VARIABLES
AcceptanceRatioOfDemandOrders(d,h)       [%]     acceptance ratio of demand orders
AcceptanceRatioOfSimpleOrders(u,h)       [%]     acceptance ratio of simple orders
AcceptanceRatioOfBlockOrders(u)          [%]     acceptance ratio of block orders
Flow(l,h)                                [MW]    Flow through lines
StorageInput(s,h)         [MWh]   Charging input for storage units
StorageOutput(s,h)
StorageLevel(s,h)         [MWh]   Storage level of charge
spillage(s,h)              [MWh]   spillage from water reservoirs
WaterSlack(s)             [MWh]   Unsatisfied water level constraint at end of optimization period
;

BINARY VARIABLE
ClearingStatusOfBlockOrder(u)                    binary variable
ClearingStatusOfFlexibleOrder(u,h)               binary variable
;

FREE VARIABLE
TotalWelfare                                     total welfate
NetPositionOfBiddingArea(n,h)            [EUR]   net position of bidding area
TemporaryNetPositionOfBiddingArea(n,h)   [EUR]   net position of bidding area
DailyNetPositionOfBiddingArea(n)
;

*===============================================================================
*Definition of lower and upper bounds
*===============================================================================
AcceptanceRatioOfDemandOrders.up(d,h) = 1;
AcceptanceRatioOfSimpleOrders.up(u,h) = 1;
AcceptanceRatioOfBlockOrders.up(u) = 1;

$offorder

*===============================================================================
*Declaration and definition of equations
*===============================================================================
EQUATIONS
EQ_Welfare         define objective function
EQ_PowerBalance_1    define power balance
EQ_PowerBalance_2    define power balance
EQ_PowerBalance_3    define power balance
EQ_Blockorder_lb   define lower bound on block order
EQ_Blockorder_ub   define uper bound on block order
EQ_Flexibleorder   define flexible order constraints
EQ_Flow_limits_ub  define upper limit on flows between zones
EQ_Flow_limits_lb  define lower limit on flows between zones
EQ_Flow_hourly_ramp_up
EQ_Flow_hourly_ramp_down
EQ_Flow_daily_ramp_up
EQ_Flow_daily_ramp_down
EQ_Node_hourly_ramp_up
EQ_Node_hourly_ramp_down
EQ_Node_daily_ramp_up
EQ_Node_daily_ramp_down
EQ_DailyNetPositionOfBiddingArea
EQ_NetPositionRamp
EQ_Unit_Ramp_Up
EQ_Unit_Ramp_Down
EQ_Storage_minimum
EQ_Storage_level
EQ_Storage_input
EQ_Storage_output
EQ_Storage_MaxDischarge
EQ_Storage_MaxCharge
EQ_Storage_balance
EQ_Storage_boundaries
;

* Objective function
EQ_Welfare ..
         TotalWelfare
         =E=
         sum((d,i), AcceptanceRatioOfDemandOrders(d,i)*AvailabilityFactorDemandOrder(d,i)*MaxDemand(d)*PriceDemandOrder(d,i))
         - sum((u,i), AcceptanceRatioOfSimpleOrders(u,i)*AvailabilityFactorSimpleOrder(u,i)*PowerCapacity(u)*PriceSimpleOrder(u,i)*OrderType(u,"Simple"))
         - sum((u,i), AcceptanceRatioOfBlockOrders(u)*AvailabilityFactorBlockOrder(u,i)*PowerCapacity(u)*PriceBlockOrder(u))
         - sum((u,i), ClearingStatusOfFlexibleOrder(u,i)*AvailabilityFactorFlexibleOrder(u)*PowerCapacity(u)*PriceFlexibleOrder(u))
         - 1000 * sum(s,WaterSlack(s));

* Neat position of each area
EQ_PowerBalance_1(n,i)..
         NetPositionOfBiddingArea(n,i)
         =E=
         sum(u, AcceptanceRatioOfSimpleOrders(u,i)*AvailabilityFactorSimpleOrder(u,i)*PowerCapacity(u)*LocationSupplySide(u,n)*OrderType(u,"Simple"))
         + sum(u, AcceptanceRatioOfBlockOrders(u)*AvailabilityFactorBlockOrder(u,i)*PowerCapacity(u)*LocationSupplySide(u,n))
         + sum(u, ClearingStatusOfFlexibleOrder(u,i)*AvailabilityFactorFlexibleOrder(u)*PowerCapacity(u)*LocationSupplySide(u,n))
         - sum(d, AcceptanceRatioOfDemandOrders(d,i)*AvailabilityFactorDemandOrder(d,i)*MaxDemand(d)*LocationDemandSide(d,n))
         - sum(s, StorageInput(s,i)*LocationSupplySide(s,n)*OrderType(s,"Storage"))
         + sum(s, StorageOutput(s,i)*LocationSupplySide(s,n)*OrderType(s,"Storage"))
;

* Net position due to flows between two areas
EQ_PowerBalance_2(n,i)..
         TemporaryNetPositionOfBiddingArea(n,i)
         =E=
         - sum(l,Flow(l,i)*LineNode(l,n));

* Net position due to flows between two areas
EQ_PowerBalance_3(n,i)..
         NetPositionOfBiddingArea(n,i)
         - TemporaryNetPositionOfBiddingArea(n,i)
         =E=
         - sum(l,Flow(l,i)*LineNode(l,n));

*Lower bound on block order
EQ_Blockorder_lb(u) ..
         AccaptanceBlockOrdersMin(u)*ClearingStatusOfBlockOrder(u)*OrderType(u,"Block")
         =L=
         AcceptanceRatioOfBlockOrders(u);

*Upper bound on block order
EQ_Blockorder_ub(u) ..
         AcceptanceRatioOfBlockOrders(u)
         =L=
         ClearingStatusOfBlockOrder(u)*OrderType(u,"Block");

*Flexible order
EQ_Flexibleorder(u) ..
         sum(i, ClearingStatusOfFlexibleOrder(u,i)*OrderType(u,"Flexible"))
         =L=
         1;

*Flows are above minimum values
EQ_Flow_limits_lb(l,i)..
         FlowMinimum(l,i)
         =L=
         Flow(l,i)
;

*Flows are below maximum values
EQ_Flow_limits_ub(l,i)..
         Flow(l,i)
         =L=
         FlowMaximum(l,i)
;

*Flows are within hourly ramping limits
EQ_Flow_hourly_ramp_up(l,i)..
         Flow(l,i)
         - Flow(l,i-1)$(ord(i) > 1) - LineInitial(l)$(ord(i) = 1)
         =L=
         LineHourlyRampUp(l,i)
;

EQ_Flow_hourly_ramp_down(l,i)..
         - Flow(l,i)
         + Flow(l,i-1)$(ord(i) > 1) + LineInitial(l)$(ord(i) = 1)
         =L=
         LineHourlyRampDown(l,i)
;

*Flows are within daily ramping limits
EQ_Flow_daily_ramp_up(l)..
         sum(i, Flow(l,i))
         =L=
         LineDailyRampUp(l)
;

EQ_Flow_daily_ramp_down(l)..
         -sum(i, Flow(l,i))
         =L=
         LineDailyRampDown(l)
;

* Net position is within hourly limits
EQ_Node_hourly_ramp_up(n,i)..
         NetPositionOfBiddingArea(n,i)
         - NetPositionOfBiddingArea(n,i-1)$(ord(i) > 1)
         =L=
         NodeHourlyRampUp(n,i)
;

EQ_Node_hourly_ramp_down(n,i)..
         - NetPositionOfBiddingArea(n,i)
         + NetPositionOfBiddingArea(n,i-1)$(ord(i) > 1)
         =L=
         NodeHourlyRampDown(n,i)
;

* Net position is within daily limits
EQ_Node_daily_ramp_up(n)..
         sum(i, NetPositionOfBiddingArea(n,i))
         =L=
         NodeDailyRampUp(n)
;

EQ_Node_daily_ramp_down(n)..
         -sum(i, NetPositionOfBiddingArea(n,i))
         =L=
         NodeDailyRampDown(n)
;

EQ_DailyNetPositionOfBiddingArea(n)..
         DailyNetPositionOfBiddingArea(n)
         =E=
         sum(i, NetPositionOfBiddingArea(n,i))
;

* Ramping rates are bound by maximum ramp up and down MW/min
EQ_Unit_Ramp_Up(u,i)$(sum(tr,Technology(u,tr))=0)..
         AcceptanceRatioOfSimpleOrders(u,i)*AvailabilityFactorSimpleOrder(u,i)*PowerCapacity(u)
         - AcceptanceRatioOfSimpleOrders(u,i-1)$(ord(i) > 1)*AvailabilityFactorSimpleOrder(u,i-1)$(ord(i) > 1)*PowerCapacity(u)
         =L=
         UnitRampUp(u)*PowerCapacity(u)
;

EQ_Unit_Ramp_Down(u,i)$(sum(tr,Technology(u,tr))=0)..
         - AcceptanceRatioOfSimpleOrders(u,i)*AvailabilityFactorSimpleOrder(u,i)*PowerCapacity(u)
         + AcceptanceRatioOfSimpleOrders(u,i-1)$(ord(i) > 1)*AvailabilityFactorSimpleOrder(u,i-1)$(ord(i) > 1)*PowerCapacity(u)
         =L=
         UnitRampDown(u)*PowerCapacity(u)
;

* Storage Related Equations
*Storage level must be above a minimum
EQ_Storage_minimum(s,i)..
         StorageMinimum(s)
         =L=
         StorageLevel(s,i)
;

*Storage level must be below storage capacity
EQ_Storage_level(s,i)..
         StorageLevel(s,i)
         =L=
         StorageCapacity(s)
;

* Storage charging is bounded by the maximum capacity
EQ_Storage_input(s,i)..
         StorageInput(s,i)
         =L=
         StorageChargingCapacity(s)
;

* Storage discharge is bounded by the maximum discharge capacity
EQ_Storage_output(s,i)..
         StorageOutput(s,i)
         =L=
         PowerCapacity(s)
;

*Discharge is limited by the storage level
EQ_Storage_MaxDischarge(s,i)$(StorageCapacity(s)>PowerCapacity(s))..
         StorageOutput(s,i)/(max(StorageDischargeEfficiency(s),0.0001))
         =L=
         StorageInitial(s)$(ord(i) = 1) + StorageLevel(s,i-1)$(ord(i) > 1)
         + StorageInflow(s,i)
;

*Charging is limited by the remaining storage capacity
EQ_Storage_MaxCharge(s,i)$(StorageCapacity(s)>PowerCapacity(s))..
         StorageInput(s,i)*StorageChargingEfficiency(s)
         =L=
         (StorageCapacity(s)-StorageInitial(s))$(ord(i) = 1)
         + (StorageCapacity(s) - StorageLevel(s,i-1))$(ord(i) > 1)
         + StorageOutflow(s,i)
;

*Storage balance
EQ_Storage_balance(s,i)..
         StorageInitial(s)$(ord(i) = 1)
         + StorageLevel(s,i-1)$(ord(i) > 1)
         + StorageInflow(s,i)
         + StorageInput(s,i)*StorageChargingEfficiency(s)
         =E=
         StorageLevel(s,i)
         + StorageOutflow(s,i)
         + spillage(s,i)
         + StorageOutput(s,i)/(max(StorageDischargeEfficiency(s),0.0001))
;

* Minimum level at the end of the optimization horizon:
EQ_Storage_boundaries(s,i)$(ord(i) = card(i))..
         StorageFinalMin(s)
         =L=
         StorageLevel(s,i) + WaterSlack(s)
;


*===============================================================================
*Definition of models
*===============================================================================
MODEL DARKO  /
EQ_Welfare
EQ_PowerBalance_1
EQ_PowerBalance_2
EQ_PowerBalance_3
EQ_Blockorder_lb
EQ_Blockorder_ub
EQ_Flexibleorder
EQ_Flow_limits_ub
EQ_Flow_limits_lb
EQ_Flow_hourly_ramp_up
EQ_Flow_hourly_ramp_down
EQ_Flow_daily_ramp_up
EQ_Flow_daily_ramp_down
EQ_Node_hourly_ramp_up
EQ_Node_hourly_ramp_down
EQ_Node_daily_ramp_up
EQ_Node_daily_ramp_down
EQ_DailyNetPositionOfBiddingArea
EQ_Unit_Ramp_Up
EQ_Unit_Ramp_Down
EQ_Storage_minimum
EQ_Storage_level
EQ_Storage_input
EQ_Storage_output
EQ_Storage_MaxDischarge
EQ_Storage_MaxCharge
EQ_Storage_balance
EQ_Storage_boundaries
/;

*===============================================================================
*Solving the models
*===============================================================================
ndays = floor(card(h)/24);
nloops = ceil(card(h)/24/Config("RollingHorizon Length","day"));

if (Config("RollingHorizon LookAhead","day") > ndays -1, abort "The look ahead period is longer than the simulation length";);
if (nloops > 10000, abort "Number of loops is longer than the maximum allowed";);

* Some parameters used for debugging:
failed=0;

* Defining a parameter that records the solver status:
set  tmp   "tpm"  / "model", "solver" /  ;
PARAMETER status(tmp,h);

* TODO: Debug section
$if %Debug% == 1 $goto DebugSection
display "OK";

* Set for the the ndays
set days /1,'ndays'/;
display days,ndays;
PARAMETER elapsed(days);

* Set for the nloops
set nlp /1*10000/;
display nlp, nloops;

* Parameters used only within loops
PARAMETER
OutputAcceptanceRatioOfBlockOrders(u, nlp)
OutputClearingStatusOfBlockOrder(u, nlp)
OutputTotalWelfare(nlp)
OutputDailyNetPositionOfBiddingArea(n,nlp)
;

cloop = 0

FOR(day = 1 TO ndays-Config("RollingHorizon LookAhead","day") by Config("RollingHorizon Length","day"),
         FirstHour = (day-1)*24+1;
         LastHour = min(card(h),FirstHour + (Config("RollingHorizon Length","day")+Config("RollingHorizon LookAhead","day"))*24 - 1);
         LastKeptHour = LastHour - Config("RollingHorizon LookAhead","day")*24;
         i(h) = no;
         i(h)$(ord(h)>=firsthour and ord(h)<=lasthour)=yes;
         display day,FirstHour,LastHour,LastKeptHour;

*        Defining the minimum level at the end of the horizon :
         StorageFinalMin(s) =  sum(i$(ord(i)=card(i)),StorageProfile(s,i)*StorageCapacity(s));


SOLVE DARKO using MIP MAXIMIZE TotalWelfare;

$If %Verbose% == 0
Display EQ_Welfare.L, EQ_PowerBalance_1.M, EQ_PowerBalance_2.M, EQ_PowerBalance_3.M, EQ_Blockorder_lb.L, EQ_Blockorder_ub.L, EQ_Flexibleorder.L, EQ_Flow_limits_ub.L, EQ_Flow_limits_lb.L;

         status("model",i) = DARKO.Modelstat;
         status("solver",i) = DARKO.Solvestat;

StorageInitial(s) =   sum(i$(ord(i)=LastKeptHour-FirstHour+1),StorageLevel.L(s,i));

* Assigning waterslack (one value per optimization horizon) to the last element of storageslack
*StorageSlack.L(s,i)$(ord(i)=LastKeptHour-FirstHour+1) =StorageSlack.L(s,i)+ Waterslack.L(s);

*Loop variables to display after solving:
$If %Verbose% == 1 Display LastKeptHour;

*Save output results for each loop:
cloop = cloop + 1;
display cloop;
OutputAcceptanceRatioOfBlockOrders(u, nlp)$(ord(nlp) = cloop) = AcceptanceRatioOfBlockOrders.L(u);
OutputClearingStatusOfBlockOrder(u, nlp)$(ord(nlp) = cloop)   = ClearingStatusOfBlockOrder.L(u);
OutputTotalWelfare(nlp)$(ord(nlp) = cloop) = TotalWelfare.L;
OutputDailyNetPositionOfBiddingArea(n,nlp)$(ord(nlp) = cloop) = DailyNetPositionOfBiddingArea.L(n);
);

*===============================================================================
*Result export
*===============================================================================
* Parameters used outside of the loops
PARAMETER
OutputAcceptanceRatioOfDemandOrders(d,h)
OutputAcceptanceRatioOfSimpleOrders(u,h)
OutputClearingStatusOfFlexibleOrder(u,h)
OutputFlow(l,h)
* Prices
OutputMarginalPrice(n,h)
OutputMarginalPrice_2(n,h)
OutputMarginalPrice_3(n,h)
OutputNetPositionOfBiddingArea(n,h)
OutputTempNetPositionOfBiddingArea(n,h)

* Storage outputs
OutputStorageMarginalPrice(s,h)
OutputStorageInput(s,h)
OutputStorageOutput(s,h)
OutputStorageLevel(s,h)
OutputSpillage(s,h)
;

OutputAcceptanceRatioOfDemandOrders(d,z) = AcceptanceRatioOfDemandOrders.L(d,z);
OutputAcceptanceRatioOfSimpleOrders(u,z) = AcceptanceRatioOfSimpleOrders.L(u,z);
OutputClearingStatusOfFlexibleOrder(u,z) = ClearingStatusOfFlexibleOrder.L(u,z);
OutputFlow(l,z) = Flow.L(l,z);
OutputMarginalPrice(n,z) = EQ_PowerBalance_1.m(n,z);
OutputMarginalPrice_2(n,z) = EQ_PowerBalance_2.m(n,z);
OutputMarginalPrice_3(n,z) = EQ_PowerBalance_3.m(n,z);
OutputNetPositionOfBiddingArea(n,z) = NetPositionOfBiddingArea.L(n,z);
OutputTempNetPositionOfBiddingArea(n,z) = TemporaryNetPositionOfBiddingArea.L(n,z);

OutputStorageMarginalPrice(s,z) = EQ_Storage_balance.m(s,z);
OutputStorageInput(s,z) = StorageInput.L(s,z);
OutputStorageOutput(s,z) = StorageOutput.L(s,z);
OutputStorageLevel(s,z) = StorageLevel.L(s,z);
OutputSpillage(s,z) = spillage.L(s,z);

EXECUTE_UNLOAD "Results.gdx"
OutputAcceptanceRatioOfDemandOrders,
OutputAcceptanceRatioOfSimpleOrders,
OutputAcceptanceRatioOfBlockOrders,
OutputClearingStatusOfBlockOrder,
OutputClearingStatusOfFlexibleOrder,
OutputFlow,
OutputMarginalPrice,
OutputMarginalPrice_2,
OutputMarginalPrice_3,
OutputNetPositionOfBiddingArea,
OutputTempNetPositionOfBiddingArea,
OutputTotalWelfare,
OutputStorageInput,
OutputStorageOutput,
OutputStorageLevel,
OutputSpillage,
OutputStorageMarginalPrice,
OutputDailyNetPositionOfBiddingArea,
status
;

$onorder

display
AcceptanceRatioOfDemandOrders.L,
AcceptanceRatioOfSimpleOrders.L,
AcceptanceRatioOfBlockOrders.L,
ClearingStatusOfBlockOrder.L,
ClearingStatusOfFlexibleOrder.L,
Flow.L,
EQ_PowerBalance_1.m,
EQ_PowerBalance_2.m,
EQ_PowerBalance_3.m,
TemporaryNetPositionOfBiddingArea.L,
NetPositionOfBiddingArea.L,
TotalWelfare.L
EQ_Flow_hourly_ramp_up.L
EQ_Flow_hourly_ramp_down.L
EQ_Flow_daily_ramp_up.L
EQ_Flow_daily_ramp_down.L
EQ_Node_hourly_ramp_up.L
EQ_Node_hourly_ramp_down.L
EQ_Node_daily_ramp_up.L
EQ_Node_daily_ramp_down.L
StorageInput.L
StorageOutput.L
StorageLevel.L
spillage.L
EQ_Storage_balance.m
