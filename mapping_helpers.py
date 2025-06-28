# -*- coding: utf-8 -*-
"""
Created on Mon Jun  9 10:15:01 2025

@author: lambe
"""

def Mapping_incomeStatement(key_needed,df):
    # Standardized name      # Possible variants (case-insensitive)
   
    mapper_IS =  
    {    
       "Revenue": [
            "Revenue", "Net sales", "Sales", "Sales and other operating revenue",
            "Total revenues net of interest expense", "Revenues", "Total net sales",
            "Total revenues", "Revenues including excise taxes"
        ],
        "OperatingIncome": [
            "Operating Income", "Income from operations", "Operating income",
            "Operating Profit", "Operating profit", "Operating earnings",
            "Operating profit (loss)", "Earnings from operations", "Operating earnings"
        ],
        "NetIncome": [
            "Net Income", "Net income", "Net earnings", "Net income (loss)",
            "Net income attributable to common stockholders", "Net earnings attributable to common stockholders",
            "Net loss", "Net earnings (loss)"
        ],
        "TotalExpenses": [
            "Total expenses", "Total operating expenses", "Total cost of sales",
            "Total costs and expenses", "Total operating costs and expenses", "TOTAL EXPENSES",
            "Total costs and other deductions", "Total expense"
        ],
        "InterestExpense": [
            "Interest Expense", "Interest expense", "Interest expense, net",
            "Interest and debt expense", "Interest and other debt expense, net",
            "Interest expense - net", "Interest (income) expense, net"
        ],
        "GrossProfit": [
            "Gross Profit", "Gross margin", "Gross profit", "Gross Profit, Total"
        ],
        "EPS_Basic": [
            "Basic (in dollars per share)", "Basic earnings per share",
            "Basic earnings per share (in dollars per share)", "Basic earnings per common share (in dollars per share)",
            "Basic Earnings Per Common Share (in dollars per share)"
        ],
        "EPS_Diluted": [
            "Diluted (in dollars per share)", "Diluted earnings per share",
            "Diluted earnings per common share (in dollars per share)", "Diluted Earnings Per Common Share (in dollars per share)"
        ],
        "R&D": [
            "Research and development", "Research and Development Expense",
            "Research, development and engineering", "Research, development and engineering expenses"
        ],
        "SGA": [
            "Selling, general and administrative", "Selling, general, administrative and development expense",
            "General and administrative", "General and administrative expense",
            "Selling, marketing, general and administrative", "General and administration",
            "General and administration expense", "Selling, general, and administrative",
            "Sales and marketing", "Marketing", "Marketing and sales",
            "Marketing expenses", "Marketing and promotion"
        ],
        "IncomeTax": [
            "Provision for income taxes", "Income Tax Expense", "Provision for (benefit from) income taxes",
            "Income tax (benefit)", "Income tax provision", "Income tax provision (benefit)",
            "Taxes on earnings", "Income taxes", "Income tax expense",
            "Income tax expense (benefit)", "INCOME TAXES", "Provision for taxes", "Tax expense"
        ]}
   
   
        pass
    
       