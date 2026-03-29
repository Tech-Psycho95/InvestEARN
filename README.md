# InvestEARN

# 📊 Mutual Fund Portfolio X-Ray

A Streamlit-based application that analyzes mutual fund portfolios from CAMS/KFintech statements and provides actionable insights for optimization.

## Features

✨ **Portfolio Reconstruction**
- Automatically extract fund names, holdings, and values from PDF statements
- Display allocation percentages across different fund categories
- Show top holdings and asset allocation breakdown

📈 **Key Metrics Analysis**
- **Expense Ratio Tracking**: Calculate total annual expense drag on your portfolio
- **XIRR Calculation**: Compute returns using the Newton-Raphson method
- **Risk Assessment**: Classify portfolio risk level based on equity/debt/liquid allocation
- **Category Analysis**: Breakdown by Large Cap, Mid Cap, Small Cap, Debt, Liquid, etc.

🔍 **Overlap Detection**
- Identify funds with similar investment mandates
- Highlight redundant holdings
- Flag high expense categories with overlap

💡 **Smart Recommendations**
- Rebalancing suggestions based on target allocation (65% Equity, 20% Debt, 15% Liquid)
- Consolidation recommendations to reduce overlap
- Expense optimization strategies
- Diversification guidance

💰 **Impact Analysis**
- Estimated annual savings from implementing recommendations
- Expense drag visualization
- Potential returns improvement insights

## Quick Start

### Installation

1. **Install Python 3.8 or higher** (if not already installed)

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

The app will open in your browser at `http://localhost:8501`

## How to Use

### Option 1: Upload Your Statement
1. Select "Upload PDF Statement" from the sidebar
2. Upload your CAMS or KFintech mutual fund statement (PDF format)
3. The app will automatically extract your portfolio data

### Option 2: View Sample Portfolio
1. Select "Sample Portfolio" from the sidebar
2. Explore the analysis with pre-loaded sample data

## Understanding the Output

### 📊 Summary Tab
- **Portfolio Overview**: Total value, number of funds, annual expense cost
- **Allocation Breakdown**: Visual and tabular breakdown by fund category
- **Top Holdings**: Your 3 largest positions

### 📈 Metrics Tab
- **Expense Analysis**: Average ER, annual cost, category-wise breakdown
- **Risk Assessment**: Equity/Debt/Liquid allocation percentages
- **Overlap Analysis**: Identifies redundant holdings

### 🎯 Recommendations Tab
- **Prioritized Actions**: 4 types of recommendations:
  - **Rebalance**: Shift between asset classes
  - **Consolidate**: Reduce overlapping funds
  - **Optimize**: Switch to lower-cost alternatives
  - **Diversify**: Add new fund categories
- **Impact Summary**: Potential annual savings and returns improvement

### 📋 Detailed Holdings Tab
- **Complete Portfolio Table**: All funds with full details
- **CSV Export**: Download your portfolio for record-keeping

## Supported Statement Formats

Currently supports multiple file formats:
- ✅ **PDF** (CAMS/KFintech portfolio statements)
- ✅ **CSV** (exported from CAMS/KFintech dashboard)
- ✅ **Excel** (XLSX/XLS files from portfolio reports)
- ✅ **Sample portfolio** (for exploration)

### How to Download Your Statement

#### Option 1: PDF Statement
1. Log in to **CAMS MF or KFintech** portal
2. Go to **My Portfolios** or **Statements**
3. Select date range and **Download PDF**
4. Upload to the app

#### Option 2: CSV Export
1. Log in to your MF dashboard
2. Navigate to **Portfolio** or **Holdings**
3. Look for **Export** or **Download**
4. Select **CSV format**
5. Upload the exported file

#### Option 3: Excel Export
1. Log in to your MF dashboard
2. View your **Portfolio Holdings**
3. Select **Export to Excel** or **Download as Excel**
4. Upload the XLSX/XLS file

### File Format Requirements

#### CSV Format
Your CSV file should have these columns (names can vary slightly):
```
Fund Name,Units,NAV,Current Value
Axis Bluechip Fund - Direct Growth,150,45.32,6798
SBI Smallcap Fund - Direct Growth,75,52.15,3911.25
```

#### Excel Format
Your Excel file should have similar columns in the first sheet:
```
| Fund Name                              | Units | NAV   | Current Value |
|----------------------------------------|-------|-------|---------------|
| Axis Bluechip Fund - Direct Growth     | 150   | 45.32 | 6798          |
| SBI Smallcap Fund - Direct Growth      | 75    | 52.15 | 3911.25       |
```

#### PDF Format
The app automatically extracts text from PDF statements. Ensure:
- PDF contains readable text (not scanned image)
- Statement shows Fund Name, Units, NAV, and Value columns
- CAMS and KFintech PDFs are fully supported

**Note:** The app intelligently detects column names, so exact naming isn't critical. Common variations are automatically recognized.

## Key Metrics Explained

### Expense Ratio (ER)
- Percentage of your investment charged annually by the fund
- Typical range: 0.15% (Liquid) to 0.65% (International, Small Cap)
- Lower is better; every 0.25% saved compounds to significant wealth

### XIRR (Extended Internal Rate of Return)
- Annualized return accounting for cash flows and timing
- Used when investments are made at different dates
- Calculated using Newton-Raphson numerical method

### Overlap Analysis
- Identifies funds investing in similar securities
- Multiple large cap funds = high overlap and redundant expense costs
- Better to consolidate into 1-2 best performers

### Allocation Categories
- **Equity (65% target)**: Large Cap, Mid Cap, Small Cap, Multi Cap
- **Debt (20% target)**: Fixed income, bonds, bond funds
- **Liquid (15% target)**: Liquid, money market funds

## Recommendation Strategy

The app recommends rebalancing based on:

1. **Asset Allocation Balance**
   - Optimal: 65% Equity, 20% Debt, 15% Liquid
   - Adjust based on your age and risk appetite

2. **Overlap Reduction**
   - Max 1-2 funds per category
   - Consolidate when overlap > 50%

3. **Expense Optimization**
   - Portfolio ER should be < 0.65%
   - Target 0.50% or lower

4. **Diversification**
   - Maintain 5-7 funds across categories
   - Avoid concentrated positions

## Example Recommendations

### ✅ Reduce Equity Exposure
*If equity >75%*
- Shift excess to debt funds for stability
- Expected benefit: Lower volatility, better sleep at night

### ✅ Reduce Small Cap Fund Overlap
*If 3+ small cap funds*
- Keep best 1-2 performers
- Consolidate others
- Expected benefit: ₹5,000-10,000 annual savings

### ✅ High Expense Ratio Drag
*If portfolio ER > 0.75%*
- Switch to index funds or lower-cost alternatives
- Expected benefit: ₹10,000-50,000+ annual savings (depending on portfolio size)

## Important Disclaimers

⚠️ **This tool provides educational insights only:**
- Uses typical expense ratios; actual may vary
- Recommendations are generic guidelines
- Past returns don't guarantee future results
- Market conditions constantly evolve
- **Always consult a qualified financial advisor** before making investment decisions

## Troubleshooting

### PDF Upload Issues
- Ensure PDF is a valid CAMS/KFintech statement
- Try extracting text manually if parsing fails
- Use sample portfolio mode to test functionality

### Missing Fund Data
- Some PDFs may have non-standard format
- App provides sample portfolio fallback
- Check if PDF is image-based (not searchable text)

### Recommendation Not Applicable
- Different recommendations suit different investor profiles
- Consider your age, goals, and risk tolerance
- Use as guidelines, not rigid rules

## Data Privacy

✅ **Your data stays private:**
- No data is sent to external servers
- All processing happens locally
- PDFs are not stored or logged

## Future Enhancements

🚀 Planned features:
- Historical return tracking (CAMS transaction history)
- Tax-loss harvesting suggestions
- Goal-based allocation recommendations
- Multi-year performance trends
- SIP optimization tools
- International fund recommendations

## Support & Feedback

For issues or feature requests:
1. Check the troubleshooting section above
2. Verify your statement format is supported
3. Try the sample portfolio for comparison

## License & Attribution

This tool is designed for retail Indian investors to better understand their mutual fund portfolios.

---

**Happy Investing! 🎯📈**

*Remember: The best portfolio is one you understand and can stick with through market cycles.*
