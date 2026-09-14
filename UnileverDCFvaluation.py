#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 13 20:16:30 2026

@author: TIAGIBSON
"""

'''
DCF Valuation Model - Unilever plc

Estimates Unilever's intrinsic share value using a discounted cash flow approach.
Projecting future free cash flow, discounting it back to present value using a real,
sourced WACC (discount rate), and comparing said result to Unilever's actual market
share price.

Data Sources:
-Unilever FY2025 Annual Report https://www.unilever.com/files/unilever-annual-report-and-accounts-2025.pdf
(Free Cash Flow, Net Debt, Underlying Sales Growth)
-Shares Outstanding https://companiesmarketcap.com/gbp/unilever/shares-outstanding/
-Shares Market price, 4th September 2026 close https://uk.finance.yahoo.com/quote/UNA.AS/
-Unilever Alphaspread https://www.alphaspread.com/security/lse/ulvr/discount-rate
(Cost of Equity, Risk-Free Rate, Beta, ERP)
-https://in.tradingview.com/symbols/DUS-XS200892127/analysis-overview , actual bond.
-https://cbonds.com/news/3933801/ States the ’S&P Global Ratings affirmed Unilever at "A+”’  and from https://www.breckinridge.com/insights/q1-2026-corporate-bond-market-outlook/  the ‘A Index (+64bps) 4 bps tighter’ where 64 bps = 0.64%, therefore take 0.6 as credit spread.
- Gov UK, Corporation Tax https://www.gov.uk/government/publications/rates-and-allowances-corporation-tax/rates-and-allowances-corporation-tax
-Stable Growth Rate https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/stablegrowthrate.htm?utm

'''
import numpy
import pandas
import matplotlib.pyplot as plt

#------------------------
# Assumptions and inputs
#------------------------
FCF = 5.9  #Free Cash Flow, EUR billions
ND = 23.1  #Net Debt, EUR billions, searched and found in FY2025
SG = 0.035  #Underlying Sales Growth, 3.5%

S_O = 2.184  #Shares Outstanding, billions
M_P = 55.48 #Shares Market Price, EUR, Close 4th September 2026

E = M_P * S_O  #Market Value of Equity (share price * total shares)
D = ND  #Market Value of Debt. The Net Debt is a reasonable stand in for this value as it's not easily attainable, finding the exact market value of the debt would require digging into Unilever's bond listings individually.
V = E + D  #Total Value of Capital

RFR = 0.035    #Risk Free Rate
BETA = 0.74    #Beta from alphaspread
ERP = 0.043    #Equity Risk Premium

Re = RFR + BETA * ERP

CS = 0.006  #Credit Spread

Rd = RFR + CS
#Rd, cost of the debt = risk free rate add credit spread
#Cross-checked against Unilever PLC 1.5% bond (ISIN: XS200892127, Düsseldorf Stock Exchange), yield to maturity ~4.08–4.09%, via TradingView.
#So, Rd is plausible.

T = 0.25  #Corporate tax, on large amount.

#Putting this all together gives us our weighted average cost of capital, our discount rate.

WACC = (E/V * Re) + (D/V * Rd * (1-T))   #WACC is approximately 6.1%

#Perpetual growth rate, pg...
pg = 0.02
# We assume that the perpetual growth rate is 0.02 as this is the goal rate of inflation, the assumed rate of inflation
# It is assumed as it is consistent with a mature company's long term sustainable growth and boadly reflects the 2% inflation targer maintained by major developed economies.

#-----------------------------
# DCF FUNCTION
#-----------------------------

def calculate_dcf(discount_rate,pgs):
    #Step 1 Project future cash flows
    assert discount_rate-0.005 > pgs, "Our perpetual growth rate cannot be too close to our discount rate else Gordon Growth model breaks down."
    # Whenever discount rate and perpetual growth rate get close, the Gordon Growth Model breaks down, this ensures that doesn't happen.

    projected_fcfs = []
    for i in range(1,9):
        fcf = FCF * (1+SG) ** i
        projected_fcfs.append(fcf)
        
    #Step 2 Discount them back to present value
    disc_fcfs=[]
    for i, value in enumerate(projected_fcfs, start = 1):
        disc_fac = 1 / (1+discount_rate)**i
        present_val = value * disc_fac
        disc_fcfs.append(present_val)
        
    Net = sum(disc_fcfs)
    
    #Step 3 Terminal Value
    fcf_9 = projected_fcfs[-1] * (1+pgs)
    TV = fcf_9/(discount_rate-pgs)
    present_TV = TV/(1+discount_rate)**8
    
    #Step 4 enterprise value -> equity value -> share price
    Enterprise_Value = Net + present_TV
    Equity_Value = Enterprise_Value - ND
    impl_share_price = Equity_Value / S_O
    
    return impl_share_price

base_case_price = calculate_dcf(WACC, pg)
print(f"Implied share price: €{base_case_price:.2f}")

#Now compare this base case to the actual market price on 4th September.
diff_pct = (base_case_price - M_P) / M_P
print(f"Actual market price: €{M_P:.2f}")
print(f"Model implies the stock is {'undervalued' if diff_pct > 0 else 'overvalued'} by {abs(diff_pct):.1%}")



#Lets do different calculation in a range now!
discount_rates = numpy.arange(WACC-0.01, WACC+0.025,0.01)

perp_growth_rates = numpy.arange(pg-0.005,pg+0.015,0.0025)

results = []

for i in discount_rates:
    row = []
    
    for p in perp_growth_rates:
        price = calculate_dcf(i, p)
        row.append(price)
    results.append(row)

df = pandas.DataFrame(results, index=[f"{dr:.1%}" for dr in discount_rates], columns=[f"{pg:.1%}" for pg in perp_growth_rates],)

print(df)

## Now lets plot the heat map

fig, ax = plt.subplots(figsize=(8,4))
im = ax.imshow(df.values, cmap='RdYlGn')

ax.set_xticks(range(len(df.columns)))
ax.set_xticklabels(df.columns)
ax.set_yticks(range(len(df.index)))
ax.set_yticklabels(df.index)

ax.set_xlabel("Perpetual Growth Rate")
ax.set_ylabel("Discount Rate")
ax.set_title('Unilever Implied Share Price Sensitivity')

fig.colorbar(im, ax=ax,label = 'Implied Share Price (EUR)')
plt.tight_layout()


for row in range(len(df.index)):
    for col in range(len(df.columns)):
        value = df.values[row, col]
        ax.text(col, row, f"{value:.0f}", ha="center", va="center", color="black")



plt.savefig("sensitivity_heatmap.png", dpi=150)
plt.show()
