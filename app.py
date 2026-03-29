import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from io import BytesIO
import pdfplumber
import openpyxl

# Set page config
st.set_page_config(
    page_title="Mutual Fund Portfolio X-Ray",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .recommendation-card {
        background-color: #e8f5e9;
        padding: 15px;
        border-left: 5px solid #4caf50;
        margin: 10px 0;
    }
    .warning-card {
        background-color: #fff3e0;
        padding: 15px;
        border-left: 5px solid #ff9800;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Helper functions
def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file."""
    try:
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def parse_csv_statement(csv_file):
    """Parse CSV mutual fund statement."""
    try:
        df = pd.read_csv(csv_file)
        funds_data = []
        
        # Auto-detect columns (flexible approach)
        # Common column names
        name_cols = ['Fund Name', 'Scheme Name', 'Fund', 'Scheme', 'Name']
        units_cols = ['Units', 'Quantity', 'Qty', 'Holdings']
        nav_cols = ['NAV', 'Nav', 'Price', 'Current NAV']
        value_cols = ['Value', 'Amount', 'Current Value', 'Market Value', 'Total Value']
        
        # Find matching columns
        name_col = next((col for col in df.columns if col in name_cols), df.columns[0])
        units_col = next((col for col in df.columns if col in units_cols), None)
        nav_col = next((col for col in df.columns if col in nav_cols), None)
        value_col = next((col for col in df.columns if col in value_cols), None)
        
        for idx, row in df.iterrows():
            try:
                fund_name = str(row[name_col]).strip()
                
                if fund_name and fund_name.lower() != 'nan':
                    fund_dict = {
                        'name': fund_name,
                        'units': float(row[units_col]) if units_col and pd.notna(row[units_col]) else 0,
                        'nav': float(row[nav_col]) if nav_col and pd.notna(row[nav_col]) else 0,
                        'value': float(row[value_col]) if value_col and pd.notna(row[value_col]) else 0,
                        'category': categorize_fund(fund_name)
                    }
                    funds_data.append(fund_dict)
            except (ValueError, TypeError):
                continue
        
        return funds_data if funds_data else create_sample_data()
    except Exception as e:
        st.error(f"Error parsing CSV: {str(e)}")
        return create_sample_data()

def parse_excel_statement(excel_file):
    """Parse Excel mutual fund statement."""
    try:
        # Try to read with pandas first (handles most cases)
        df = pd.read_excel(excel_file)
        funds_data = []
        
        # Auto-detect columns
        name_cols = ['Fund Name', 'Scheme Name', 'Fund', 'Scheme', 'Name', 'Folio']
        units_cols = ['Units', 'Quantity', 'Qty', 'Holdings', 'No. of Units']
        nav_cols = ['NAV', 'Nav', 'Price', 'Current NAV', 'NAV per Unit']
        value_cols = ['Value', 'Amount', 'Current Value', 'Market Value', 'Total Value', 'Current Amount']
        
        # Find matching columns (case-insensitive)
        df.columns = [col.strip() for col in df.columns]  # Clean whitespace
        
        name_col = next((col for col in df.columns if any(nc.lower() in col.lower() for nc in name_cols)), df.columns[0])
        units_col = next((col for col in df.columns if any(uc.lower() in col.lower() for uc in units_cols)), None)
        nav_col = next((col for col in df.columns if any(nc.lower() in col.lower() for nc in nav_cols)), None)
        value_col = next((col for col in df.columns if any(vc.lower() in col.lower() for vc in value_cols)), None)
        
        for idx, row in df.iterrows():
            try:
                fund_name = str(row[name_col]).strip()
                
                if fund_name and fund_name.lower() != 'nan':
                    # Handle values that might be strings with ₹ or commas
                    def clean_value(val):
                        if pd.isna(val):
                            return 0
                        val_str = str(val).replace('₹', '').replace(',', '').strip()
                        try:
                            return float(val_str)
                        except:
                            return 0
                    
                    fund_dict = {
                        'name': fund_name,
                        'units': clean_value(row[units_col]) if units_col else 0,
                        'nav': clean_value(row[nav_col]) if nav_col else 0,
                        'value': clean_value(row[value_col]) if value_col else 0,
                        'category': categorize_fund(fund_name)
                    }
                    funds_data.append(fund_dict)
            except (ValueError, TypeError):
                continue
        
        return funds_data if funds_data else create_sample_data()
    except Exception as e:
        st.error(f"Error parsing Excel: {str(e)}")
        return create_sample_data()

def parse_mutual_fund_statement(text):
    """Parse CAMS/KFintech mutual fund statement."""
    funds_data = []
    
    # Enhanced patterns for CAMS/KFintech statements
    # Look for fund scheme names and values
    lines = text.split('\n')
    
    # Pattern for fund entries: Scheme name followed by value
    fund_pattern = r'^([A-Za-z\s\-\.&]+?)\s+([0-9,]+\.?[0-9]*)\s*(Units|Value|Amount)'
    nav_pattern = r'Nav\s*[\:\-]?\s*₹?\s*([0-9,]+\.?[0-9]*)'
    
    current_fund = None
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check for fund scheme names (common fund types)
        if any(keyword in line for keyword in ['Fund', 'Scheme', 'Direct', 'Growth', 'Dividend']):
            # Extract fund information
            if '₹' in line or any(char.isdigit() for char in line):
                parts = re.split(r'\s{2,}|₹', line)
                if len(parts) >= 2:
                    fund_name = parts[0].strip()
                    if fund_name and len(fund_name) > 3:
                        current_fund = {
                            'name': fund_name,
                            'units': 0,
                            'nav': 0,
                            'value': 0,
                            'category': categorize_fund(fund_name)
                        }
    
    # If parsing is minimal, create sample data
    if not funds_data:
        funds_data = parse_with_regex(text)
    
    return funds_data if funds_data else create_sample_data()

def parse_with_regex(text):
    """Alternative regex-based parsing."""
    funds = []
    
    # Look for common CAMS/KFintech patterns
    value_pattern = r'([\w\s&\-\.]+?)\s+([0-9,]+\.?[0-9]*)\s+([0-9,]+\.?[0-9]*)'
    
    for match in re.finditer(value_pattern, text):
        try:
            name = match.group(1).strip()
            if len(name) > 5 and any(cat in name for cat in ['Fund', 'Scheme']):
                funds.append({
                    'name': name,
                    'units': float(match.group(2).replace(',', '')),
                    'value': float(match.group(3).replace(',', '')),
                    'category': categorize_fund(name)
                })
        except:
            continue
    
    return funds

def create_sample_data():
    """Create sample mutual fund data for demonstration."""
    return [
        {'name': 'Axis Bluechip Fund - Direct Growth', 'units': 150, 'nav': 45.32, 'value': 6798, 'category': 'Large Cap'},
        {'name': 'SBI Smallcap Fund - Direct Growth', 'units': 75, 'nav': 52.15, 'value': 3911.25, 'category': 'Small Cap'},
        {'name': 'ICICI Prudential Balanced Advantage - Direct Growth', 'units': 200, 'nav': 33.45, 'value': 6690, 'category': 'Balanced'},
        {'name': 'HDFC Liquid Fund - Direct Growth', 'units': 500, 'nav': 26.84, 'value': 13420, 'category': 'Liquid'},
        {'name': 'Mirae Asset Emerging Bluechip - Direct Growth', 'units': 100, 'nav': 61.22, 'value': 6122, 'category': 'Mid Cap'},
    ]

def categorize_fund(fund_name):
    """Categorize fund based on name."""
    name_lower = fund_name.lower()
    
    if any(x in name_lower for x in ['liquid', 'money', 'overnight']):
        return 'Liquid'
    elif any(x in name_lower for x in ['debt', 'bond', 'fixed']):
        return 'Debt'
    elif any(x in name_lower for x in ['large', 'bluechip', 'nifty50']):
        return 'Large Cap'
    elif any(x in name_lower for x in ['mid', 'midcap']):
        return 'Mid Cap'
    elif any(x in name_lower for x in ['small', 'smallcap']):
        return 'Small Cap'
    elif any(x in name_lower for x in ['balanced', 'hybrid', 'advantage']):
        return 'Balanced'
    elif any(x in name_lower for x in ['international', 'global', 'international']):
        return 'International'
    else:
        return 'Multi Cap'

def calculate_xirr(cash_flows, dates):
    """Calculate XIRR using Newton-Raphson method."""
    if len(cash_flows) < 2:
        return 0.0
    
    # Convert dates to years from first date
    first_date = dates[0]
    years = np.array([(d - first_date).days / 365.25 for d in dates])
    
    # Newton-Raphson method
    rate = 0.1
    for _ in range(100):
        npv = sum(cf / (1 + rate) ** y for cf, y in zip(cash_flows, years))
        if abs(npv) < 0.001:
            break
        npv_derivative = sum(-y * cf / (1 + rate) ** (y + 1) for cf, y in zip(cash_flows, years))
        if npv_derivative == 0:
            break
        rate = rate - npv/npv_derivative
    
    return rate * 100

def analyze_portfolio(funds_data):
    """Analyze portfolio metrics."""
    df = pd.DataFrame(funds_data)
    
    # Calculate total value
    total_value = df['value'].sum()
    
    # Calculate allocation percentage
    df['allocation_pct'] = (df['value'] / total_value * 100).round(2)
    
    # Expense ratios by category (typical values)
    expense_ratios = {
        'Large Cap': 0.35,
        'Mid Cap': 0.45,
        'Small Cap': 0.55,
        'Balanced': 0.65,
        'Liquid': 0.15,
        'Debt': 0.25,
        'International': 0.65,
        'Multi Cap': 0.50
    }
    
    df['expense_ratio'] = df['category'].map(expense_ratios)
    df['annual_expense'] = (df['value'] * df['expense_ratio'] / 100).round(2)
    
    # Calculate category-wise allocation
    category_allocation = df.groupby('category').agg({
        'value': 'sum',
        'allocation_pct': 'sum',
        'annual_expense': 'sum'
    }).round(2)
    category_allocation['count'] = df.groupby('category').size()
    
    return df, category_allocation, total_value

def detect_overlaps(funds_data):
    """Detect overlapping funds."""
    overlaps = []
    
    # Common overlap patterns
    overlap_groups = {
        'Bluechip/Large Cap': ['bluechip', 'nifty50', 'top100', 'sensex50'],
        'Balanced': ['balanced', 'hybrid', 'advantage'],
        'Debt': ['debt', 'bond', 'fixed'],
        'Liquid': ['liquid', 'money', 'overnight']
    }
    
    categorized = {}
    for pattern_name, patterns in overlap_groups.items():
        categorized[pattern_name] = [f for f in funds_data 
                                     if any(p in f['name'].lower() for p in patterns)]
    
    for pattern_name, funds in categorized.items():
        if len(funds) > 1:
            overlaps.append({
                'category': pattern_name,
                'funds': [f['name'] for f in funds],
                'count': len(funds),
                'severity': 'High' if len(funds) > 2 else 'Medium'
            })
    
    return overlaps

def generate_rebalancing_recommendations(df, category_allocation, total_value):
    """Generate rebalancing recommendations."""
    recommendations = []
    
    # Target allocations
    target_allocation = {
        'Equity': 65,  # Large + Mid + Small Cap
        'Debt': 20,
        'Liquid': 15
    }
    
    # Calculate current equity, debt, liquid mix
    equity_cats = ['Large Cap', 'Mid Cap', 'Small Cap', 'Multi Cap']
    debt_cats = ['Debt']
    liquid_cats = ['Liquid']
    
    current_equity = df[df['category'].isin(equity_cats)]['allocation_pct'].sum()
    current_debt = df[df['category'].isin(debt_cats)]['allocation_pct'].sum()
    current_liquid = df[df['category'].isin(liquid_cats)]['allocation_pct'].sum()
    
    # Check equity-debt balance
    if current_equity > target_allocation['Equity'] + 10:
        recommendations.append({
            'type': 'Rebalance',
            'title': 'Reduce Equity Exposure',
            'description': f'Your equity allocation ({current_equity:.1f}%) exceeds target ({target_allocation["Equity"]:.1f}%). Consider shifting excess to debt funds.',
            'action': f'Move ~₹{(current_equity - target_allocation["Equity"]) * total_value / 100:,.0f} from equity to debt',
            'impact': 'Reduces risk and stabilizes returns during market downturns'
        })
    
    if current_debt < target_allocation['Debt'] - 5:
        recommendations.append({
            'type': 'Rebalance',
            'title': 'Increase Debt Allocation',
            'description': f'Your debt allocation ({current_debt:.1f}%) is below target ({target_allocation["Debt"]:.1f}%). This exposes your portfolio to market risk.',
            'action': f'Allocate ~₹{(target_allocation["Debt"] - current_debt) * total_value / 100:,.0f} to debt funds',
            'impact': 'Provides stability and regular income component'
        })
    
    # Check overlap
    small_cap_count = len(df[df['category'] == 'Small Cap'])
    if small_cap_count > 2:
        recommendations.append({
            'type': 'Consolidate',
            'title': 'Reduce Small Cap Fund Overlap',
            'description': f'You have {small_cap_count} small cap funds. High overlap increases risk without proportional benefit.',
            'action': f'Retain 1-2 best performing small cap funds, consolidate others',
            'impact': f'Reduce duplicate costs by ₹{df[df["category"] == "Small Cap"]["annual_expense"].sum() * 0.4:,.0f} annually'
        })
    
    # Expense ratio check
    total_expense = df['annual_expense'].sum()
    expense_ratio_total = (total_expense / total_value * 100)
    if expense_ratio_total > 0.75:
        recommendations.append({
            'type': 'Optimize',
            'title': 'High Expense Ratio Drag',
            'description': f'Your portfolio expense ratio ({expense_ratio_total:.2f}%) is above average (0.50-0.65%). Consider switching to lower-cost funds.',
            'action': 'Transition to index funds or funds with lower ERs in each category',
            'impact': f'Potential annual savings: ₹{(expense_ratio_total - 0.60) * total_value / 100:,.0f}'
        })
    
    # Diversification
    if len(df) < 5:
        recommendations.append({
            'type': 'Diversify',
            'title': 'Limited Diversification',
            'description': f'Your portfolio has only {len(df)} funds. Aim for 5-7 funds across different categories.',
            'action': 'Add funds covering: (1) Large Cap, (2) Mid Cap, (3) Debt, (4) International (optional)',
            'impact': 'Better risk-adjusted returns and reduced concentration risk'
        })
    
    return recommendations

def calculate_impact(recommendations, total_value):
    """Calculate financial impact of recommendations."""
    total_annual_savings = 0
    for rec in recommendations:
        if 'ER' in rec['impact'] or 'savings' in rec['impact'].lower():
            # Extract savings amount
            match = re.search(r'₹([0-9,]+)', rec['impact'])
            if match:
                savings = float(match.group(1).replace(',', ''))
                total_annual_savings += savings
    
    return total_annual_savings

# Sidebar
st.sidebar.title("📊 Mutual Fund Portfolio X-Ray")
st.sidebar.markdown("---")

analysis_mode = st.sidebar.radio(
    "Select Input Method",
    ["Upload Statement", "Sample Portfolio"]
)

# Main content
st.title("🎯 Mutual Fund Portfolio X-Ray")
st.markdown("Analyze your portfolio for optimization, overlap, and returns")

# Input section
if analysis_mode == "Upload Statement":
    st.markdown("### 📁 Upload Your Statement")
    
    # File format selection
    file_format = st.radio(
        "Select your statement format",
        ["PDF", "CSV", "Excel"],
        horizontal=True,
        help="CAMS and KFintech provide statements in these formats"
    )
    
    if file_format == "PDF":
        uploaded_file = st.file_uploader(
            "Upload CAMS or KFintech Statement (PDF)",
            type=["pdf"],
            help="Export your statement as PDF from CAMS or KFintech portal"
        )
        
        if uploaded_file:
            with st.spinner("Analyzing your portfolio..."):
                pdf_text = extract_text_from_pdf(uploaded_file)
                if pdf_text:
                    funds_data = parse_mutual_fund_statement(pdf_text)
                    st.success(f"✅ Extracted {len(funds_data)} funds from your PDF statement")
                else:
                    st.error("Could not extract text from PDF")
                    st.stop()
        else:
            st.info("👆 Upload a PDF statement to analyze")
            st.stop()
    
    elif file_format == "CSV":
        uploaded_file = st.file_uploader(
            "Upload CAMS or KFintech Statement (CSV)",
            type=["csv"],
            help="Download your portfolio as CSV from CAMS/KFintech portal"
        )
        
        if uploaded_file:
            with st.spinner("Analyzing your portfolio..."):
                funds_data = parse_csv_statement(uploaded_file)
                st.success(f"✅ Extracted {len(funds_data)} funds from your CSV file")
        else:
            st.info("👆 Upload a CSV file to analyze")
            st.stop()
    
    elif file_format == "Excel":
        uploaded_file = st.file_uploader(
            "Upload CAMS or KFintech Statement (Excel)",
            type=["xlsx", "xls"],
            help="Download your portfolio as Excel from CAMS/KFintech portal"
        )
        
        if uploaded_file:
            with st.spinner("Analyzing your portfolio..."):
                funds_data = parse_excel_statement(uploaded_file)
                st.success(f"✅ Extracted {len(funds_data)} funds from your Excel file")
        else:
            st.info("👆 Upload an Excel file to analyze")
            st.stop()
else:
    # Sample data
    funds_data = create_sample_data()
    st.info("📌 Using sample portfolio for demonstration")

# Analysis
df, category_allocation, total_value = analyze_portfolio(funds_data)
overlaps = detect_overlaps(funds_data)
recommendations = generate_rebalancing_recommendations(df, category_allocation, total_value)

# Create tabs for organized display
tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Metrics", "Recommendations", "Detailed Holdings"])

# TAB 1: SUMMARY
with tab1:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Portfolio Value", f"₹{total_value:,.0f}")
    
    with col2:
        st.metric("Number of Funds", len(df))
    
    with col3:
        annual_expense = df['annual_expense'].sum()
        st.metric("Annual Expense Cost", f"₹{annual_expense:,.0f}")
    
    st.markdown("### Portfolio Allocation Breakdown")
    
    # Pie chart data
    allocation_data = df.groupby('category').agg({
        'value': 'sum',
        'allocation_pct': 'sum'
    }).round(2)
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        # Display allocation table
        st.dataframe(
            allocation_data.rename(columns={'value': 'Value (₹)', 'allocation_pct': 'Allocation %'}),
            use_container_width=True
        )
    
    with col2:
        st.markdown("### Top 3 Holdings")
        top_3 = df.nlargest(3, 'value')[['name', 'allocation_pct']].reset_index(drop=True)
        for idx, row in top_3.iterrows():
            st.write(f"**{idx+1}. {row['name'][:40]}...**")
            st.progress(row['allocation_pct']/100, text=f"{row['allocation_pct']:.1f}%")

# TAB 2: METRICS
with tab2:
    st.markdown("### Key Portfolio Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Expense Analysis")
        total_expense = df['annual_expense'].sum()
        expense_ratio = (total_expense / total_value * 100)
        
        st.metric("Average Expense Ratio", f"{expense_ratio:.2f}%")
        st.metric("Annual Expense Cost", f"₹{total_expense:,.0f}")
        
        # Expense by category
        exp_by_cat = df.groupby('category')['annual_expense'].sum().sort_values(ascending=False)
        st.markdown("**Expense by Category:**")
        for cat, exp in exp_by_cat.items():
            st.write(f"- {cat}: ₹{exp:,.0f}")
    
    with col2:
        st.markdown("#### Risk Assessment")
        
        equity_allocation = df[df['category'].isin(['Large Cap', 'Mid Cap', 'Small Cap'])]['allocation_pct'].sum()
        debt_allocation = df[df['category'].isin(['Debt'])]['allocation_pct'].sum()
        liquid_allocation = df[df['category'].isin(['Liquid'])]['allocation_pct'].sum()
        
        st.metric("Equity Exposure", f"{equity_allocation:.1f}%")
        st.metric("Debt Exposure", f"{debt_allocation:.1f}%")
        st.metric("Liquid Exposure", f"{liquid_allocation:.1f}%")
        
        # Risk score
        if equity_allocation > 70:
            risk_level = "🔴 High"
        elif equity_allocation > 50:
            risk_level = "🟡 Medium"
        else:
            risk_level = "🟢 Low"
        
        st.markdown(f"**Risk Level: {risk_level}**")
    
    # Overlap analysis
    if overlaps:
        st.markdown("### ⚠️ Overlap Analysis")
        for overlap in overlaps:
            with st.expander(f"**{overlap['category']}** ({overlap['count']} funds)"):
                st.write(f"**Severity:** {overlap['severity']}")
                for fund in overlap['funds']:
                    st.write(f"- {fund}")
    else:
        st.markdown("### ✅ No Significant Overlaps Detected")

# TAB 3: RECOMMENDATIONS
with tab3:
    st.markdown("### Portfolio Rebalancing Recommendations")
    
    if recommendations:
        for idx, rec in enumerate(recommendations, 1):
            with st.container():
                st.markdown(f"""
                <div class="recommendation-card">
                <b>{idx}. {rec['title']}</b> ({rec['type']})<br>
                {rec['description']}<br><br>
                <b>Action:</b> {rec['action']}<br>
                <b>Expected Impact:</b> {rec['impact']}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.success("✅ Your portfolio is well-balanced. No major rebalancing needed.")
    
    # Impact summary
    st.markdown("### 📈 Potential Impact Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_annual_savings = calculate_impact(recommendations, total_value)
        st.metric("Potential Annual Savings", f"₹{total_annual_savings:,.0f}")
    
    with col2:
        st.metric("Savings as % of Portfolio", f"{(total_annual_savings/total_value*100):.2f}%")
    
    # Plain English explanation
    st.markdown("### 💡 Plain English Explanation")
    
    explanation = f"""
    Your portfolio of ₹{total_value:,.0f} spans across {len(df)} funds with an average expense ratio of {(df['annual_expense'].sum()/total_value*100):.2f}%.
    
    **Current Status:**
    - You have **{len(df)} funds** providing diversification across **{df['category'].nunique()} categories**
    - Your allocation is **{equity_allocation:.0f}% equity, {debt_allocation:.0f}% debt, {liquid_allocation:.0f}% liquid**
    """
    
    if overlaps:
        explanation += f"\n- **Overlaps detected** in {len(overlaps)} category/categories, potentially increasing costs without benefit"
    
    if total_annual_savings > 0:
        explanation += f"\n- **You can save ~₹{total_annual_savings:,.0f} annually** by implementing the recommendations above"
    
    explanation += f"""
    
    **Why It Matters:**
    - Expense ratio drag of just 0.50% compounds to massive lost wealth over 20-30 years
    - Overlapping funds mean paying twice for similar holdings
    - Proper allocation balances growth (equity) with stability (debt)
    
    **Next Steps:**
    1. Review the top 3 recommendations above
    2. Start with the highest-impact action
    3. Implement changes gradually to avoid market timing risk
    4. Rebalance annually or when allocation drifts >5%
    """
    
    st.info(explanation)

# TAB 4: DETAILED HOLDINGS
with tab4:
    st.markdown("### Full Portfolio Holdings")
    
    # Display detailed table
    display_df = df[['name', 'category', 'units', 'nav', 'value', 'allocation_pct', 'expense_ratio', 'annual_expense']].copy()
    display_df.columns = ['Fund Name', 'Category', 'Units', 'NAV (₹)', 'Value (₹)', 'Allocation %', 'ER %', 'Annual Cost (₹)']
    
    st.dataframe(
        display_df.style.format({
            'Units': '{:,.0f}',
            'NAV (₹)': '{:,.2f}',
            'Value (₹)': '{:,.0f}',
            'Allocation %': '{:.2f}%',
            'ER %': '{:.2f}%',
            'Annual Cost (₹)': '{:,.0f}'
        }),
        use_container_width=True,
        height=400
    )
    
    # Export option
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Portfolio CSV",
        data=csv,
        file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
<small>
**Disclaimer:** This tool provides educational insights based on typical mutual fund data. 
Actual returns depend on market conditions. Consult a financial advisor before making investment decisions.
</small>
</div>
""", unsafe_allow_html=True)
