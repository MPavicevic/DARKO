.. _model:

Model Description
=================

The model is expressed as a MILP problem.

Variables
^^^^^^^^^

Sets
----

======= =================================================================================
Name	Description
======= =================================================================================
u       Units Supply Side
d       ProsumersConsumers Demand Side
o       Order type
n       Nodes
l       Lines
t       Technologies
tr(t)   Renewable technologies
f       Fuel types
s(u)    Storage Technologies
h       Hours
i(h)    Subset of simulated hours for one iteration
z(h)    Subset of all simulated hours
sk      Sectors
======= =================================================================================

Parameters
----------

======================================= ========== =============================================================
Name                                    Units      Description
======================================= ========== =============================================================
**Availabilities**
AccaptanceBlockOrdersMin(u)              [%]       Accaptance ratio for block orders
AvailabilityFactorDemandOrder(d,h)       [%]       Share of maximum demand in time period h
AvailabilityFactorSimpleOrder(u,h)       [%]       Share of maximum Simple order in time period h
AvailabilityFactorBlockOrder(u,h)        [%]       Share of maximum Block order in time period h
AvailabilityFactorFlexibleOrder(u)       [%]       Accaptance ratio for block orders

**Node data**
LocationDemandSide(d,n)                  [n.a.]    Location               {1 0}
LocationSupplySide(u,n)                  [n.a.]    Location               {1 0}
NodeHourlyRampUp(n, h)                   [%\h\n]   Node ramp up limit
NodeHourlyRampDown(n, h)                 [%\h\n]   Node ramp down limit
NodeDailyRampUp(n)                       [%\24h\n] Node daily ramp up limit
NodeDailyRampDown(n)                     [%\24h\n] Node daily ramp up limit
NodeInitial(n)

**Prices**
PriceDemandOrder(d,h)                    [€\MW]    Price ofer of the consumer d in time period h
PriceSimpleOrder(u,h)                    [€\MW]    Price ofer of the simple order u in time period h
PriceBlockOrder(u)                       [€\MW]    Default block order price
PriceFlexibleOrder(u)                    [€\MW]    Default block order price

**Interconection lines**
LineNode(l,n)                            [n.a.]    Incidence matrix       {-1 +1}
FlowMaximum(l,h)                         [MW]      Line limits
FlowMinimum(l,h)                         [MW]      Minimum flow
LineHourlyRampUp(l, h)                   [%\h\n]   Interconection line ramp up limit
LineHourlyRampDown(l, h)                 [%\h\n]   Interconection line ramp down limit
LineDailyRampUp(l)                       [%\24h\n] Interconection daily line ramp up limit
LineDailyRampDown(l)                     [%\24h\n] Interconection daily line ramp down limit
LineInitial(l)

**Units / demands**
MaxDemand(d)                             [MW\u]    Maximum demand
PowerCapacity(u)                         [MW\u]    Installed capacity
OrderType(u,o)                           [n.a.]    Order type             {1 0}
Technology(u,t)                          [n.a.]    Technology type        {1 0}
Fuel(u,f)                                [n.a.]    Fuel type              {1 0}
Sector(d,sk)                             [n.a.]    Demand sector type     {1 0}
UnitRampUp(u)                            [%\h\u]   Unit ramp up limit
UnitRampDown(u)                          [%\h\u]   Unit ramp down limit
LinkedBlockOrderIncidenceMatrix(u)
MinimumIncomeFixed(u)
MinimumIncomeVariable(u)

**Storage**
StorageChargingCapacity(s)               [MW\u]    Storage capacity
StorageChargingEfficiency(s)             [%]       Charging efficiency
StorageSelfDischarge(s)                  [%\day]   Self-discharge of the storage units
StorageCapacity(s)                       [MWh\u]   Storage capacity
StorageDischargeEfficiency(s)            [%]       Discharge efficiency
StorageOutflow(s,h)                      [MWh\u]   Storage outflows
StorageInflow(s,h)                       [MWh\u]   Storage inflows (potential energy)
StorageInitial(s)                        [MWh]     Storage level before initial period
StorageProfile(s,h)                      [%]       Storage level to be resepected at the end of each horizon
StorageMinimum(s)                        [MWh]     Storage minimum
StorageFinalMin(s)                       [MWh]     Minimum storage level at the end of the optimization horizon
======================================= ========== =============================================================

NB: When the parameter is expressed per unit ("/u"), its value must be provided for one single unit.

Positive Optimization Variables
-------------------------------

==================================== ======= =============================================================
Name                                 Units   Description
==================================== ======= =============================================================
AcceptanceRatioOfDemandOrders(d,h)   [%]     Acceptance ratio of demand orders
AcceptanceRatioOfSimpleOrders(u,h)   [%]     Acceptance ratio of simple orders
AcceptanceRatioOfBlockOrders(u)      [%]     Acceptance ratio of block orders
Flow(l,h)                            [MW]    Flow through lines
StorageInput(s,h)                    [MW]    Charging input for storage units
StorageOutput(s,h)                   [MW]    Discharging output for storage units
StorageLevel(s,h)                    [MWh]   Storage level of charge
spillage(s,h)                        [MW]    Spillage from reservoirs
WaterSlack(s)                        [MWh]   Unsatisfied water level constraint at end of optimization period
SystemCost(h)                        [EUR]   Hourly system cost
==================================== ======= =============================================================

Binary Variables
-----------------

=================================== ======= =============================================================
Name                                Units   Description
=================================== ======= =============================================================
ClearingStatusOfBlockOrder(u)       -       Binary variable
ClearingStatusOfFlexibleOrder(u,h)  -       Binary variable
=================================== ======= =============================================================

Free Variables
--------------
====================================== ======= =============================================================
Name                                   Units   Description
====================================== ======= =============================================================
TotalWelfare                             [EUR]   Total welfate
NetPositionOfBiddingArea(n,h)            [EUR]   Net position of bidding area
TemporaryNetPositionOfBiddingArea(n,h)   [EUR]   Temporary net position of bidding area
DailyNetPositionOfBiddingArea(n)         [EUR]   Daily net position of biding area
====================================== ======= =============================================================


Optimisation model
^^^^^^^^^^^^^^^^^^

Objective function
------------------

The goal of the day-ahead market problem is to maximize the total welfare.

.. math::
	\begin{align}
	max TotalWelfare = \sum_{i} SystemCost_{i} - \sum_{s} StorageSlack_{s}
	\end{align}

System costs
------------

Hourly system costs are defined as follows:

.. math::
	\begin{split}
	& \mathit{SystemCost}_{i} = \\
	\sum_{d} (& AcceptanceRatioOfDemandOrders_{d,i} \cdot AvailabilityFactorDemandOrder_{d,i} \cdot \\
	& MaxDemand_{d} \cdot PriceDemandOrder_{d,i}) \\
	- \sum_{u} (& AcceptanceRatioOfSimpleOrders_{u,i} \cdot AvailabilityFactorSimpleOrder_{u,i} \cdot \\
	& PowerCapacity_{u} \cdot PriceSimpleOrder_{u,i}) \\ 
	- \sum_{u} (& AcceptanceRatioOfBlockOrders_{u,i} \cdot AvailabilityFactorBlockOrder_{u,i} \cdot \\
	& PowerCapacity_{u} \cdot PriceBlockOrder_{u}) \\
	- \sum_{u} (& AcceptanceRatioOfFlexibleOrders_{u,i} \cdot AvailabilityFactorFlexibleOrder_{u,i} \cdot \\
	& PowerCapacity_{u} \cdot PriceFlexibleOrderOrder_{u}) \\
	\end{split}

Power Balances
--------------

The main constraint to be met is the supply-demand balance, for each period and each zone, in the day-ahead market (equation ). 
According to this restriction, the sum of all the power produced by all the units present in the node (including the power generated by the storage units), the power injected from neighbouring nodes is equal to the 
load in that node plus the power consumed for energy storage

Net position of each area:

.. math::
	\begin{split}
	& \mathit{NetPositionOfBiddingArea}_{n,i} = \\
	\sum_{u} (& AcceptanceRatioOfSimpleOrders_{u,i} \cdot AvailabilityFactorSimpleOrder_{u,i} \cdot \\
	& PowerCapacity_{u} \cdot LocationSupplySide_{u,n}) \\ 
	+ \sum_{u} (& AcceptanceRatioOfBlockOrders_{u,i} \cdot AvailabilityFactorBlockOrder_{u,i} \cdot \\
	& PowerCapacity_{u} \cdot LocationSupplySide_{u,n}) \\ 
	+ \sum_{u} (& AcceptanceRatioOfFlexibleOrders_{u,i} \cdot AvailabilityFactorFlexibleOrder_{u,i} \cdot \\
	& PowerCapacity_{u} \cdot LocationSupplySide_{u,n}) \\ 
	- \sum_{d} (& AcceptanceRatioOfDemandOrders_{d,i} \cdot AvailabilityFactorDemandOrder_{d,i} \cdot \\
	& MaxDemand_{d} \cdot LocationDemandSide_{d,n}) \\
	- \sum_{s} (& StorageInput_{s,i} \cdot LocationSupplySide_{s,n}) \\
	+ \sum_{s} (& StorageOutput_{s,i} \cdot LocationSupplySide_{s,n})
	\end{split}

Temporary net position due to flows between two neighbouring areas:

.. math::
	\begin{split}
	& TemporaryNetPositionOfBiddingArea_{n,i} = - \sum_{l} (Flow(l,i) \cdot LineNode_{l,n})
	\end{split}

Net position due to flows between two neighbouring areas:

.. math::
	\begin{split}
	& NetPositionOfBiddingArea_{n,i} - TemporaryNetPositionOfBiddingArea_{n,i} = \\
	& - \sum_{l} (Flow_{l,i} \cdot LineNode_{l,n})
	\end{split}

Block orders
------------

Lower and upper bounds on block orders:

.. math::
	AccaptanceBlockOrdersMin_{u} \cdot ClearingStatusOfBlockOrder_{u} \cdot OrderType_{u,"Block"} \leq \\
	AcceptanceRatioOfBlockOrders_{u}
	
.. math::
	AcceptanceRatioOfBlockOrders_{u} \leq \\
	AccaptanceBlockOrdersMin_{u} \cdot ClearingStatusOfBlockOrder_{u} \cdot OrderType_{u,"Block"}


Flexible orders
---------------

Limits of flexible orders

.. math::
	\begin{split}
	& \sum_{i} (ClearingStatusOfFlexibleOrder_{u,i} \cdot OrderType_{u,"Flexible"}) \leq 1
	\end{split}


Flow limits
-----------

Flows are above minimum values

.. math::
	FlowMinimum_{l,i} \leq Flow_{l,i}


Flows are below maximum values

.. math::
	Flow_{l,i} \leq FlowMaximum_{l,i}


Flows are within hourly ramping limits

.. math::
	Flow_{l,i} - Flow_{l,i-1} - LineInitial_{l,i=1} \leq LineHourlyRampUp_{l,i}

.. math::

    - Flow_{l,i} + Flow_{l,i-1} + LineInitial_{l,i=1} \leq LineHourlyRampDown_{l,i}


Flows are within daily ramping limits

.. math::
	\sum_{i} (Flow_{l,i}) \leq LineDailyRampUp_{l}


.. math::
	- \sum_{i} (Flow_{l,i}) \leq LineDailyRampDown{l};

Net position limits
-------------------

Net position is within hourly limits

.. math::
	NetPositionOfBiddingArea_{n,i} - NetPositionOfBiddingArea_{n,i-1} \\
	\leq NodeHourlyRampUp_{n,i}
	

.. math::
	- NetPositionOfBiddingArea_{n,i} + NetPositionOfBiddingArea_{n,i-1} \\
	\leq NodeHourlyRampDown_{n,i}
	

Net position is bounded by net position ramping limits

.. math::
	\sum_{i} (NetPositionOfBiddingArea_{n,i}) \leq NodeDailyRampUp_{n}
	
.. math::
	- \sum_{i} (NetPositionOfBiddingArea_{n,i}) \leq NodeDailyRampDown_{n}

Net position is within daily limits

.. math::
	DailyNetPositionOfBiddingArea_{n} \leq \sum_{i} (NetPositionOfBiddingArea_{n,i})

Ramping rates
-------------

Ramping rates are bound by maximum ramp up and down MW/min

.. math::
	\begin{split}
	& AcceptanceRatioOfSimpleOrders_{u,i} \cdot AvailabilityFactorSimpleOrder_{u,i} \\  
	& \cdot PowerCapacity_{u} \\
    & - AcceptanceRatioOfSimpleOrders_{u,i-1} \cdot AvailabilityFactorSimpleOrder_{u,i-1} \\
	& \cdot PowerCapacity_{u} \\
	& \leq UnitRampUp_{u} \cdot PowerCapacity_{u}
	\end{split}
	
.. math::
	\begin{split}
	& AcceptanceRatioOfSimpleOrders_{u,i-1} \cdot AvailabilityFactorSimpleOrder_{u,i-1} \\ 
	& \cdot PowerCapacity_{u} \\ 
	& - AcceptanceRatioOfSimpleOrders_{u,i} \cdot AvailabilityFactorSimpleOrder_{u,i} \\
	& \cdot PowerCapacity_{u} \\
	& \leq UnitRampDown_{u} \cdot PowerCapacity_{u}
	\end{split}

Storage-related constraints
---------------------------

Generation units with energy storage capabilities (large hydro reservoirs, pumped hydro storage units, hydrogen storage units or batteries) must meet additional restrictions related to the amount of energy stored. Storage units are considered to be subject to the same constraints as non-storage power plants. In addition to those constraints, storage-specific restrictions are added for the set of storage units (i.e. a subset of all units). These restrictions include the storage capacity, inflow, outflow, charging, charging capacity, charge/discharge efficiencies, etc. Discharging is considered as the standard operation mode and is therefore linked to the Power variable, common to all units.

The first constraint imposes that the energy stored by a given unit is bounded by a minimum value:

.. math::

	\mathit{StorageMinimum}_s \leq \mathit{StorageLevel}_{s,i}

In the case of a storage unit, the availability factor applies to the charging/discharging power, but also to the storage capacity. The storage level is thus limited by:

.. math::

	\mathit{StorageLevel}_{s,i} \leq \mathit{StorageCapacity}_s

The energy added to the storage unit is limited by the charging capacity. Charging is allowed only if the unit is not producing (discharging) at the same time (i.e. if Committed, corresponding to the normal mode, is equal to 0).

.. math::

	\mathit{StorageInput}_{s,i} \leq \mathit{StorageChargingCapacity}_s

Discharge is limited by the level of charge of the storage unit:

.. math::

	\frac{\mathit{StorageOutput}_{s,i}}{\mathit{StorageDischargeEfficiency}_s} 
	\leq \mathit{StorageLevel}_{s,i-1} + \mathit{StorageInflow}_{s,i}
	

It is worthwhile to note that StorageInflow and StorageOuflow must be multiplied by the number of units because they are defined for a single storage plant. On the contrary StorageLevel, Spillage and Power are defined for all units s. 
StorageInflow and Storage Outflow are predefined time series, whose meaning depends on the type of storage units: for hydro units, it is the natural water flows. For hydrogen units, StorageInflow is 0 at all times, but StorageOutflow represents the hydrogen demand (for fuel cell vehicles, industries,...). For batteries, both parameters are null at all times.

Charge is limited by the level of charge of the storage unit:

.. math::

	\mathit{StorageInput}_{s,i} \cdot \mathit{StorageChargingEfficiency}_s 
	
	\leq \mathit{StorageCapacity}_s - \mathit{StorageLevel}_{s,i} + StorageOutflow_{s,i}
	

Besides, the energy stored in a given period is given by the energy stored in the previous period, net of charges and discharges. This is storage balance equation:

.. math::
	
	\mathit{StorageLevel}_{s,i-1} + \mathit{StorageInflow}_{s,i} + \mathit{StorageInput}_{s,i} \cdot \mathit{StorageChargingEfficiency}_s

	= \mathit{StorageLevel}_{s,i} + \mathit{StorageOutflow}_{s,i} + Spillage_{wat,i} + \frac{\mathit{StorageOutput}_{s,i}}{\mathit{StorageDischargeEfficienc}y_s}

Some storage units are equiped with large reservoirs, whose capacity at full load might be longer than the optimisation horizon. Therefore, a minimum level constraint is required for the last hour of the optimisation, which otherwise would systematically tend to empty the reservoir as much a possible. An exogenous minimum profile is thus provided and the following constraint is applied:

.. math::
	StorageFinalMin_{s} \leq StorageLevel_{s,i} + StorageSlack_{s}



where N is the last period of the optimization horizon, StorageProfile is a non-dimensional minimum storage level provided as an exogenous input and StorageSlack is a variable defining the unsatified water level. The price associated to that water is very high.



Rolling Horizon
^^^^^^^^^^^^^^^
The mathematical problem described in the previous sections could in principle be solved for a whole year split into time steps, but with all likelihood the problem would become extremely demanding in computational terms when attempting to solve the model with a realistically sized dataset. Therefore, the problem is split into smaller optimization problems that are run recursively throughout the year. 

The following figure shows an example of such approach, in which the optimization horizon is two days, including a look-ahead (or overlap) period of one day. The initial values of the optimization for day j are the final values of the optimization of the previous day. The look-ahead period is modelled to avoid issues related to the end of the optimization period such as emptying the hydro reservoirs, or starting low-cost but non-flexible power plants. In this case, the optimization is performed over 48 hours, but only the first 24 hours are conserved.

##.. image:: figures/rolling_horizon.png

The optimization horizon and overlap period can be adjusted by the user in the DARKO configuration file. As a rule of thumb, the optimization horizon plus the overlap period should at least be twice the maximum duration of the time-dependent constraints (e.g. the minimum up and down times). In terms of computational efficiency, small power systems can be simulated with longer optimization horizons, while larger systems should reduce this horizon, the minimum being one day.


References
^^^^^^^^^^
