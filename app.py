import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Nassau Candy Profitability Dashboard",
    page_icon="🍫",
    layout="wide"
)


# ============================================================
# 2. TITLE
# ============================================================

st.title("Nassau Candy Distributor")
st.subheader("Product Line Profitability & Margin Performance Analysis")

st.markdown(
    """
    Interactive dashboard for analyzing product profitability,
    division performance, cost structure, revenue concentration,
    geographic performance, and factory performance.
    """
)


# ============================================================
# 3. LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    return pd.read_csv("Nassau Candy Distributor.csv")


df = load_data()


# ============================================================
# 4. DATA PREPARATION
# ============================================================

# Convert Order Date
# Dates are day-first (DD-MM-YYYY); without dayfirst=True ~60% fail to parse
df["Order Date"] = pd.to_datetime(
    df["Order Date"],
    dayfirst=True,
    errors="coerce"
)
df = df.dropna(subset=["Order Date"])

# Gross Profit
df["Gross Profit"] = df["Sales"] - df["Cost"]

# Gross Margin %
df["Gross Margin %"] = np.where(
    df["Sales"] != 0,
    (df["Gross Profit"] / df["Sales"]) * 100,
    0
)

# Profit per Unit
df["Profit per Unit"] = np.where(
    df["Units"] != 0,
    df["Gross Profit"] / df["Units"],
    0
)

# Order Year
df["Order Year"] = df["Order Date"].dt.year


# ============================================================
# 5. SIDEBAR FILTERS
# ============================================================

st.sidebar.header("Dashboard Filters")

# Date filter
min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()

date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Division filter
division_options = ["All"] + sorted(
    df["Division"].dropna().unique().tolist()
)

selected_division = st.sidebar.selectbox(
    "Division",
    division_options
)

# Margin filter
margin_threshold = st.sidebar.slider(
    "Minimum Gross Margin (%)",
    min_value=0.0,
    max_value=100.0,
    value=0.0,
    step=1.0
)
# Product Search
product_search = st.sidebar.text_input(
    "Product Search",
    placeholder="Search for a product..."
)



# ============================================================
# 6. APPLY FILTERS
# ============================================================

filtered_df = df.copy()

# Date filter
if len(date_range) == 2:

    start_date = date_range[0]
    end_date = date_range[1]

    filtered_df = filtered_df[
        (filtered_df["Order Date"].dt.date >= start_date)
        &
        (filtered_df["Order Date"].dt.date <= end_date)
    ]

# Division filter
if selected_division != "All":

    filtered_df = filtered_df[
        filtered_df["Division"] == selected_division
    ]

# Product search
if product_search:
    filtered_df = filtered_df[
        filtered_df["Product Name"].str.contains(
            product_search,
            case=False,
            na=False,
            regex=False
        )
    ]

# Margin threshold: applied at PRODUCT level (aggregate margin of each
# product within the selected dates/division), not to individual order rows
_pm = filtered_df.groupby("Product Name")[["Sales", "Gross Profit"]].sum()
_pm["m"] = np.where(_pm["Sales"] != 0, _pm["Gross Profit"] / _pm["Sales"] * 100, 0)
filtered_df = filtered_df[
    filtered_df["Product Name"].isin(_pm[_pm["m"] >= margin_threshold].index)
]

# Guard: stop gracefully if filters leave no data
if filtered_df.empty:
    st.warning("No records match the current filters. Please widen the date range, division, search or margin threshold.")
    st.stop()


# ============================================================
# 7. KEY PERFORMANCE INDICATORS
# ============================================================

total_revenue = filtered_df["Sales"].sum()

total_cost = filtered_df["Cost"].sum()

total_profit = filtered_df["Gross Profit"].sum()

total_units = filtered_df["Units"].sum()

gross_margin = (
    total_profit / total_revenue * 100
    if total_revenue != 0
    else 0
)

profit_per_unit = (
    total_profit / total_units
    if total_units != 0
    else 0
)


# ============================================================
# 8. KPI DISPLAY
# ============================================================

st.markdown("## Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Total Revenue",
    f"${total_revenue:,.0f}"
)

col2.metric(
    "Total Cost",
    f"${total_cost:,.0f}"
)

col3.metric(
    "Gross Profit",
    f"${total_profit:,.0f}"
)

col4.metric(
    "Gross Margin",
    f"{gross_margin:.1f}%"

)

col5.metric(
    "Profit per Unit",
    f"${profit_per_unit:,.2f}"
)


# ============================================================
# 9. BASIC DATA INFORMATION
# ============================================================

st.markdown("## Dashboard Overview")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Products",
    filtered_df["Product Name"].nunique()
)

col2.metric(
    "Divisions",
    filtered_df["Division"].nunique()
)

col3.metric(
    "States",
    filtered_df["State/Province"].nunique()
)


# ============================================================
# 10. FILTERED DATA
# ============================================================

with st.expander("View Filtered Data"):

    st.dataframe(
        filtered_df,
        width="stretch"
    )
    # ============================================================
# 11. PRODUCT PROFITABILITY OVERVIEW
# ============================================================

st.markdown("## 1. Product Profitability Overview")

st.markdown(
    """
    This section evaluates product-level revenue, gross profit,
    gross margin, profit per unit, and contribution to overall
    profitability.
    """
)


# ------------------------------------------------------------
# PRODUCT-LEVEL AGGREGATION
# ------------------------------------------------------------

product_analysis = filtered_df.groupby(
    "Product Name"
).agg(
    Total_Sales=("Sales", "sum"),
    Total_Cost=("Cost", "sum"),
    Total_Gross_Profit=("Gross Profit", "sum"),
    Total_Units=("Units", "sum")
).reset_index()


# Gross Margin
product_analysis["Gross_Margin_%"] = np.where(
    product_analysis["Total_Sales"] != 0,
    (
        product_analysis["Total_Gross_Profit"]
        / product_analysis["Total_Sales"]
    ) * 100,
    0
)


# Profit per Unit
product_analysis["Profit_per_Unit"] = np.where(
    product_analysis["Total_Units"] != 0,
    (
        product_analysis["Total_Gross_Profit"]
        / product_analysis["Total_Units"]
    ),
    0
)


# Revenue Contribution
total_filtered_sales = product_analysis["Total_Sales"].sum()

product_analysis["Revenue_Contribution_%"] = np.where(
    total_filtered_sales != 0,
    (
        product_analysis["Total_Sales"]
        / total_filtered_sales
    ) * 100,
    0
)


# Profit Contribution
total_filtered_profit = product_analysis["Total_Gross_Profit"].sum()

product_analysis["Profit_Contribution_%"] = np.where(
    total_filtered_profit != 0,
    (
        product_analysis["Total_Gross_Profit"]
        / total_filtered_profit
    ) * 100,
    0
)


# ------------------------------------------------------------
# MARGIN VOLATILITY (std. dev. of monthly margin, in percentage points)
# ------------------------------------------------------------

_monthly = filtered_df.assign(
    Month=filtered_df["Order Date"].dt.to_period("M")
).groupby(["Product Name", "Month"])[["Sales", "Gross Profit"]].sum().reset_index()

_monthly["m"] = _monthly["Gross Profit"] / _monthly["Sales"] * 100

_vol = _monthly.groupby("Product Name")["m"].std().fillna(0).round(2)
_vol = _vol.rename("Margin_Volatility").reset_index()

product_analysis = product_analysis.merge(_vol, on="Product Name", how="left")

st.metric(
    "Average Margin Volatility (pp, monthly)",
    f"{product_analysis['Margin_Volatility'].mean():.2f}"
)
if product_analysis["Margin_Volatility"].max() < 0.05:
    st.caption(
        "Margin volatility is ~0 for every product: unit prices and costs are "
        "fixed, so margin differences between products are structural, not time-driven."
    )

# ------------------------------------------------------------
# PRODUCT PERFORMANCE CLASSIFICATION
# ------------------------------------------------------------

sales_median = product_analysis["Total_Sales"].median()

margin_median = product_analysis["Gross_Margin_%"].median()


def classify_product(row):

    high_sales = row["Total_Sales"] >= sales_median
    high_margin = row["Gross_Margin_%"] >= margin_median

    if high_sales and high_margin:
        return "High Sales / High Margin"

    elif high_sales and not high_margin:
        return "High Sales / Low Margin"

    elif not high_sales and high_margin:
        return "Low Sales / High Margin"

    else:
        return "Low Sales / Low Margin"


product_analysis["Profitability_Class"] = product_analysis.apply(
    classify_product,
    axis=1
)


# ------------------------------------------------------------
# TOP PRODUCTS BY GROSS PROFIT
# ------------------------------------------------------------

st.markdown("### Top Products by Gross Profit")

top_profit_products = product_analysis.sort_values(
    "Total_Gross_Profit",
    ascending=False
).head(10)


fig_profit = px.bar(
    top_profit_products.sort_values("Total_Gross_Profit"),
    x="Total_Gross_Profit",
    y="Product Name",
    orientation="h",
    title="Top 10 Products by Gross Profit",
    labels={
        "Total_Gross_Profit": "Gross Profit",
        "Product Name": "Product"
    }
)

st.plotly_chart(
    fig_profit,
    width="stretch"
)


# ------------------------------------------------------------
# TOP PRODUCTS BY GROSS MARGIN
# ------------------------------------------------------------

st.markdown("### Products by Gross Margin")

top_margin_products = product_analysis.sort_values(
    "Gross_Margin_%",
    ascending=False
)


fig_margin = px.bar(
    top_margin_products,
    x="Gross_Margin_%",
    y="Product Name",
    orientation="h",
    title="Products Ranked by Gross Margin",
    labels={
        "Gross_Margin_%": "Gross Margin (%)",
        "Product Name": "Product"
    }
)

fig_margin.update_layout(
    yaxis={"categoryorder": "total ascending"}
)

st.plotly_chart(
    fig_margin,
    width="stretch"
)


# ------------------------------------------------------------
# PROFITABILITY MATRIX
# ------------------------------------------------------------

st.markdown("### Product Profitability Matrix")

fig_matrix = px.scatter(
    product_analysis,
    x="Total_Sales",
    y="Gross_Margin_%",
    size="Total_Gross_Profit",
    hover_name="Product Name",
    hover_data=[
        "Total_Gross_Profit",
        "Profit_per_Unit",
        "Revenue_Contribution_%",
        "Profit_Contribution_%",
        "Profitability_Class"
    ],
    title="Sales vs Gross Margin",
    labels={
        "Total_Sales": "Total Sales",
        "Gross_Margin_%": "Gross Margin (%)"
    }
)

fig_matrix.add_vline(
    x=sales_median,
    line_dash="dash",
    annotation_text="Median Sales"
)

fig_matrix.add_hline(
    y=margin_median,
    line_dash="dash",
    annotation_text="Median Margin"
)

st.plotly_chart(
    fig_matrix,
    width="stretch"
)

# ------------------------------------------------------------
# PRODUCT PROFITABILITY TABLE
# ------------------------------------------------------------

st.markdown("### Product Profitability Details")

display_columns = [
    "Product Name",
    "Total_Sales",
    "Total_Gross_Profit",
    "Gross_Margin_%",
    "Profit_per_Unit",
    "Revenue_Contribution_%",
    "Profit_Contribution_%",
    "Margin_Volatility",
    "Profitability_Class"
]

product_table = product_analysis[
    display_columns
].sort_values(
    "Total_Gross_Profit",
    ascending=False
).copy()


# Round numerical values
product_table["Total_Sales"] = product_table["Total_Sales"].round(2)
product_table["Total_Gross_Profit"] = product_table["Total_Gross_Profit"].round(2)
product_table["Gross_Margin_%"] = product_table["Gross_Margin_%"].round(1)
product_table["Profit_per_Unit"] = product_table["Profit_per_Unit"].round(2)
product_table["Revenue_Contribution_%"] = product_table["Revenue_Contribution_%"].round(1)
product_table["Profit_Contribution_%"] = product_table["Profit_Contribution_%"].round(1)


st.dataframe(
    product_table,
    width="stretch",
    hide_index=True
)
# ============================================================
# 12. DIVISION PERFORMANCE
# ============================================================

st.markdown("## 2. Division Performance")

st.markdown(
    """
    This section compares revenue, cost, gross profit, and gross
    margin across the major product divisions.
    """
)


# ------------------------------------------------------------
# DIVISION-LEVEL AGGREGATION
# ------------------------------------------------------------

division_analysis = filtered_df.groupby(
    "Division"
).agg(
    Total_Sales=("Sales", "sum"),
    Total_Cost=("Cost", "sum"),
    Total_Gross_Profit=("Gross Profit", "sum"),
    Total_Units=("Units", "sum")
).reset_index()


# Gross Margin
division_analysis["Gross_Margin_%"] = np.where(
    division_analysis["Total_Sales"] != 0,
    (
        division_analysis["Total_Gross_Profit"]
        / division_analysis["Total_Sales"]
    ) * 100,
    0
)


# Revenue Contribution
division_analysis["Revenue_Contribution_%"] = (
    division_analysis["Total_Sales"]
    / division_analysis["Total_Sales"].sum()
) * 100


# Profit Contribution
division_analysis["Profit_Contribution_%"] = (
    division_analysis["Total_Gross_Profit"]
    / division_analysis["Total_Gross_Profit"].sum()
) * 100


# ------------------------------------------------------------
# REVENUE VS PROFIT
# ------------------------------------------------------------

st.markdown("### Revenue vs Gross Profit by Division")

division_chart_data = division_analysis.melt(
    id_vars="Division",
    value_vars=[
        "Total_Sales",
        "Total_Gross_Profit"
    ],
    var_name="Metric",
    value_name="Amount"
)

division_chart_data["Metric"] = division_chart_data[
    "Metric"
].replace({
    "Total_Sales": "Revenue",
    "Total_Gross_Profit": "Gross Profit"
})


fig_division = px.bar(
    division_chart_data,
    x="Division",
    y="Amount",
    color="Metric",
    barmode="group",
    title="Revenue vs Gross Profit by Division",
    labels={
        "Amount": "Amount",
        "Division": "Division"
    }
)

st.plotly_chart(
    fig_division,
    width="stretch"
)


# ------------------------------------------------------------
# GROSS MARGIN BY DIVISION
# ------------------------------------------------------------

st.markdown("### Gross Margin by Division")

fig_division_margin = px.bar(
    division_analysis.sort_values(
        "Gross_Margin_%",
        ascending=True
    ),
    x="Gross_Margin_%",
    y="Division",
    orientation="h",
    title="Gross Margin by Division",
    labels={
        "Gross_Margin_%": "Gross Margin (%)",
        "Division": "Division"
    }
)

st.plotly_chart(
    fig_division_margin,
    width="stretch"
)


# ------------------------------------------------------------
# MARGIN DISTRIBUTION BY DIVISION
# ------------------------------------------------------------

st.markdown("### Margin Distribution by Division")

_pd = filtered_df.groupby(["Division", "Product Name"])[["Sales", "Gross Profit"]].sum().reset_index()
_pd["Gross_Margin_%"] = _pd["Gross Profit"] / _pd["Sales"] * 100

fig_div_box = px.box(
    _pd,
    x="Division",
    y="Gross_Margin_%",
    points="all",
    hover_name="Product Name",
    title="Product Gross Margin Distribution by Division",
    labels={"Gross_Margin_%": "Gross Margin (%)"}
)

st.plotly_chart(fig_div_box, width="stretch")

# ------------------------------------------------------------
# DIVISION PROFITABILITY TABLE
# ------------------------------------------------------------

st.markdown("### Division Performance Details")

division_table = division_analysis[
    [
        "Division",
        "Total_Sales",
        "Total_Cost",
        "Total_Gross_Profit",
        "Gross_Margin_%",
        "Revenue_Contribution_%",
        "Profit_Contribution_%",
        "Total_Units"
    ]
].sort_values(
    "Total_Gross_Profit",
    ascending=False
).copy()


# Round values
division_table["Total_Sales"] = division_table["Total_Sales"].round(2)
division_table["Total_Cost"] = division_table["Total_Cost"].round(2)
division_table["Total_Gross_Profit"] = division_table[
    "Total_Gross_Profit"
].round(2)

division_table["Gross_Margin_%"] = division_table[
    "Gross_Margin_%"
].round(1)

division_table["Revenue_Contribution_%"] = division_table[
    "Revenue_Contribution_%"
].round(1)

division_table["Profit_Contribution_%"] = division_table[
    "Profit_Contribution_%"
].round(1)


st.dataframe(
    division_table,
    width="stretch",
    hide_index=True
)
# ============================================================
# 13. COST VS MARGIN DIAGNOSTICS
# ============================================================

st.markdown("## 3. Cost vs Margin Diagnostics")

st.markdown(
    """
    This section evaluates the relationship between product cost,
    sales, and gross margin to identify cost-heavy and
    margin-poor products that may require management attention.
    """
)


# ------------------------------------------------------------
# PRODUCT COST ANALYSIS
# ------------------------------------------------------------

cost_analysis = filtered_df.groupby(
    "Product Name"
).agg(
    Total_Sales=("Sales", "sum"),
    Total_Cost=("Cost", "sum"),
    Total_Gross_Profit=("Gross Profit", "sum"),
    Total_Units=("Units", "sum")
).reset_index()


cost_analysis["Gross_Margin_%"] = np.where(
    cost_analysis["Total_Sales"] != 0,
    (
        cost_analysis["Total_Gross_Profit"]
        / cost_analysis["Total_Sales"]
    ) * 100,
    0
)


cost_analysis["Cost_to_Sales_%"] = np.where(
    cost_analysis["Total_Sales"] != 0,
    (
        cost_analysis["Total_Cost"]
        / cost_analysis["Total_Sales"]
    ) * 100,
    0
)


cost_analysis["Profit_per_Unit"] = np.where(
    cost_analysis["Total_Units"] != 0,
    (
        cost_analysis["Total_Gross_Profit"]
        / cost_analysis["Total_Units"]
    ),
    0
)


# ------------------------------------------------------------
# COST VS SALES SCATTER
# ------------------------------------------------------------

st.markdown("### Cost vs Sales")

fig_cost_sales = px.scatter(
    cost_analysis,
    x="Total_Sales",
    y="Total_Cost",
    size="Total_Gross_Profit",
    hover_name="Product Name",
    hover_data=[
        "Total_Gross_Profit",
        "Gross_Margin_%",
        "Cost_to_Sales_%",
        "Profit_per_Unit"
    ],
    title="Product Cost vs Sales",
    labels={
        "Total_Sales": "Total Sales",
        "Total_Cost": "Total Cost"
    }
)

# Reference line: Cost = Sales
max_value = max(
    cost_analysis["Total_Sales"].max(),
    cost_analysis["Total_Cost"].max()
)

fig_cost_sales.add_shape(
    type="line",
    x0=0,
    y0=0,
    x1=max_value,
    y1=max_value,
    line_dash="dash"
)

st.plotly_chart(
    fig_cost_sales,
    width="stretch"
)


# ------------------------------------------------------------
# COST-TO-SALES RATIO
# ------------------------------------------------------------

st.markdown("### Cost-to-Sales Ratio by Product")

cost_ratio_chart = cost_analysis.sort_values(
    "Cost_to_Sales_%",
    ascending=True
)


fig_cost_ratio = px.bar(
    cost_ratio_chart,
    x="Cost_to_Sales_%",
    y="Product Name",
    orientation="h",
    title="Cost-to-Sales Ratio",
    labels={
        "Cost_to_Sales_%": "Cost-to-Sales (%)",
        "Product Name": "Product"
    }
)

st.plotly_chart(
    fig_cost_ratio,
    width="stretch"
)


# ------------------------------------------------------------
# LOW-MARGIN PRODUCTS
# ------------------------------------------------------------

st.markdown("### Low-Margin Products")

low_margin_products = cost_analysis.sort_values(
    "Gross_Margin_%",
    ascending=True
).head(5)


fig_low_margin = px.bar(
    low_margin_products.sort_values(
        "Gross_Margin_%"
    ),
    x="Gross_Margin_%",
    y="Product Name",
    orientation="h",
    title="Lowest-Margin Products",
    labels={
        "Gross_Margin_%": "Gross Margin (%)",
        "Product Name": "Product"
    }
)

st.plotly_chart(
    fig_low_margin,
    width="stretch"
)


# ------------------------------------------------------------
# COST DIAGNOSTIC TABLE
# ------------------------------------------------------------

st.markdown("### Cost & Margin Diagnostic Table")

cost_table = cost_analysis[
    [
        "Product Name",
        "Total_Sales",
        "Total_Cost",
        "Total_Gross_Profit",
        "Gross_Margin_%",
        "Cost_to_Sales_%",
        "Profit_per_Unit"
    ]
].sort_values(
    "Gross_Margin_%",
    ascending=True
).copy()


cost_table["Total_Sales"] = cost_table[
    "Total_Sales"
].round(2)

cost_table["Total_Cost"] = cost_table[
    "Total_Cost"
].round(2)

cost_table["Total_Gross_Profit"] = cost_table[
    "Total_Gross_Profit"
].round(2)

cost_table["Gross_Margin_%"] = cost_table[
    "Gross_Margin_%"
].round(1)

cost_table["Cost_to_Sales_%"] = cost_table[
    "Cost_to_Sales_%"
].round(1)

cost_table["Profit_per_Unit"] = cost_table[
    "Profit_per_Unit"
].round(2)


st.dataframe(
    cost_table,
    width="stretch",
    hide_index=True
)
# ------------------------------------------------------------
# MARGIN RISK FLAGS
# ------------------------------------------------------------

st.markdown("### Margin Risk Flags")

LOW_MARGIN = 20      # % margin below which a product is considered margin-poor
COST_GAP = 10        # pp cost-to-sales above division average => renegotiate
SMALL_SHARE = 2      # % revenue share below which a product is "small"

_flags = cost_analysis.merge(
    filtered_df.groupby("Product Name")["Division"].first().reset_index(),
    on="Product Name"
)

_div = _flags.groupby("Division")[["Total_Cost", "Total_Sales"]].sum()
_div["div_cost_ratio"] = _div["Total_Cost"] / _div["Total_Sales"] * 100
_flags = _flags.merge(_div[["div_cost_ratio"]], on="Division")
_flags["Revenue_Share_%"] = _flags["Total_Sales"] / _flags["Total_Sales"].sum() * 100


def risk_flag(r):
    actions = []
    if r["Gross_Margin_%"] < LOW_MARGIN:
        actions.append("Reprice")
        if r["Revenue_Share_%"] < SMALL_SHARE:
            actions.append("Discontinuation review")
    if r["Cost_to_Sales_%"] > r["div_cost_ratio"] + COST_GAP:
        actions.append("Cost renegotiation")
    return ", ".join(actions) if actions else "OK"


_flags["Risk_Flag"] = _flags.apply(risk_flag, axis=1)

st.caption(
    f"Rules: margin < {LOW_MARGIN}% -> Reprice (plus Discontinuation review if revenue "
    f"share < {SMALL_SHARE}%); cost-to-sales more than {COST_GAP} pp above the "
    f"division average -> Cost renegotiation."
)

_risk_table = _flags[[
    "Product Name", "Division", "Total_Sales", "Gross_Margin_%",
    "Cost_to_Sales_%", "Revenue_Share_%", "Risk_Flag"
]].sort_values("Gross_Margin_%").round(2)

st.dataframe(_risk_table, width="stretch", hide_index=True)

_n_risk = int((_flags["Risk_Flag"] != "OK").sum())
st.metric("Products Flagged", _n_risk)


# ============================================================
# 14. PROFIT CONCENTRATION & PARETO ANALYSIS
# ============================================================



st.markdown("## 4. Profit Concentration & Pareto Analysis")

st.markdown(
    """
    Pareto analysis identifies how strongly revenue and gross profit
    are concentrated among a small number of products. This helps
    assess dependency and concentration risk.
    """
)


# ------------------------------------------------------------
# PRODUCT-LEVEL DATA
# ------------------------------------------------------------

pareto_analysis = filtered_df.groupby(
    "Product Name"
).agg(
    Total_Sales=("Sales", "sum"),
    Total_Gross_Profit=("Gross Profit", "sum")
).reset_index()



# ============================================================
# REVENUE PARETO
# ============================================================

st.markdown("### Revenue Pareto Analysis")

revenue_pareto = pareto_analysis.sort_values(
    "Total_Sales",
    ascending=False
).reset_index(drop=True)

total_revenue_pareto = revenue_pareto[
    "Total_Sales"
].sum()

revenue_pareto["Revenue_Contribution_%"] = (
    revenue_pareto["Total_Sales"]
    / total_revenue_pareto
) * 100

revenue_pareto["Cumulative_Revenue_%"] = (
    revenue_pareto["Revenue_Contribution_%"]
    .cumsum()
)


# Number of products needed to reach 80% revenue
revenue_80_index = (
    revenue_pareto["Cumulative_Revenue_%"] >= 80
).idxmax()

n_for_80_revenue = revenue_80_index + 1


st.metric(
    "Products Required for 80% of Revenue",
    n_for_80_revenue
)


fig_revenue_pareto = px.bar(
    revenue_pareto,
    x="Product Name",
    y="Total_Sales",
    title="Revenue Pareto Analysis",
    labels={
        "Total_Sales": "Revenue",
        "Product Name": "Product"
    }
)

fig_revenue_pareto.update_layout(
    xaxis_tickangle=-45
)

fig_revenue_pareto.add_hline(
    y=total_revenue_pareto * 0.80,
    line_dash="dash",
    annotation_text="80% of Total Revenue"
)

fig_revenue_pareto.add_trace(go.Scatter(
    x=revenue_pareto["Product Name"],
    y=revenue_pareto["Cumulative_Revenue_%"],
    name="Cumulative %",
    yaxis="y2",
    mode="lines+markers"
))
fig_revenue_pareto.update_layout(
    yaxis2=dict(overlaying="y", side="right", range=[0, 105], title="Cumulative %")
)

st.plotly_chart(
    fig_revenue_pareto,
    width="stretch"
)


# ============================================================
# PROFIT PARETO
# ============================================================

st.markdown("### Profit Pareto Analysis")

profit_pareto = pareto_analysis.sort_values(
    "Total_Gross_Profit",
    ascending=False
).reset_index(drop=True)

total_profit_pareto = profit_pareto[
    "Total_Gross_Profit"
].sum()

profit_pareto["Profit_Contribution_%"] = (
    profit_pareto["Total_Gross_Profit"]
    / total_profit_pareto
) * 100

profit_pareto["Cumulative_Profit_%"] = (
    profit_pareto["Profit_Contribution_%"]
    .cumsum()
)


# Number of products needed to reach 80% profit
profit_80_index = (
    profit_pareto["Cumulative_Profit_%"] >= 80
).idxmax()

n_for_80_profit = profit_80_index + 1


st.metric(
    "Products Required for 80% of Gross Profit",
    n_for_80_profit
)


fig_profit_pareto = px.bar(
    profit_pareto,
    x="Product Name",
    y="Total_Gross_Profit",
    title="Profit Pareto Analysis",
    labels={
        "Total_Gross_Profit": "Gross Profit",
        "Product Name": "Product"
    }
)

fig_profit_pareto.update_layout(
    xaxis_tickangle=-45
)

fig_profit_pareto.add_hline(
    y=total_profit_pareto * 0.80,
    line_dash="dash",
    annotation_text="80% of Total Gross Profit"
)

fig_profit_pareto.add_trace(go.Scatter(
    x=profit_pareto["Product Name"],
    y=profit_pareto["Cumulative_Profit_%"],
    name="Cumulative %",
    yaxis="y2",
    mode="lines+markers"
))
fig_profit_pareto.update_layout(
    yaxis2=dict(overlaying="y", side="right", range=[0, 105], title="Cumulative %")
)

st.plotly_chart(
    fig_profit_pareto,
    width="stretch"
)


# ============================================================
# DEPENDENCY INDICATORS
# ============================================================

st.markdown("### Dependency Indicators")

_shares = profit_pareto["Profit_Contribution_%"] / 100
top1_share = _shares.iloc[0] * 100
top3_share = _shares.head(3).sum() * 100
top5_share = _shares.head(5).sum() * 100
hhi = float((_shares ** 2).sum() * 10000)   # Herfindahl-Hirschman index (0-10,000)

if top3_share >= 50 or top5_share >= 80 or hhi >= 2500:
    dep_level = "HIGH"
elif top3_share >= 35 or top5_share >= 60 or hhi >= 1500:
    dep_level = "MODERATE"
else:
    dep_level = "LOW"

d1, d2, d3, d4, d5 = st.columns(5)
d1.metric("Top Product Profit Share", f"{top1_share:.1f}%")
d2.metric("Top 3 Products Profit Share", f"{top3_share:.1f}%")
d3.metric("Top 5 Products Profit Share", f"{top5_share:.1f}%")
d4.metric("Profit HHI", f"{hhi:,.0f}")
d5.metric("Dependency Risk", dep_level)

st.caption(
    "Risk level: HIGH if top-3 share >= 50%, top-5 share >= 80% or HHI >= 2,500; "
    "MODERATE if top-3 >= 35%, top-5 >= 60% or HHI >= 1,500; otherwise LOW."
)

# ============================================================
# REVENUE VS PROFIT CONCENTRATION
# ============================================================

st.markdown("### Revenue vs Profit Concentration")

concentration_summary = pd.DataFrame({
    "Metric": [
        "Products for 80% Revenue",
        "Products for 80% Gross Profit"
    ],
    "Number of Products": [
        n_for_80_revenue,
        n_for_80_profit
    ]
})


fig_concentration = px.bar(
    concentration_summary,
    x="Metric",
    y="Number of Products",
    title="Products Required to Generate 80% of Revenue vs Profit",
    text="Number of Products",
    labels={
        "Number of Products": "Number of Products"
    }
)

fig_concentration.update_traces(
    textposition="outside"
)

st.plotly_chart(
    fig_concentration,
    width="stretch"
)


# ============================================================
# PROFIT CONCENTRATION TABLE
# ============================================================

st.markdown("### Profit Concentration Details")

profit_table = profit_pareto[
    [
        "Product Name",
        "Total_Gross_Profit",
        "Profit_Contribution_%",
        "Cumulative_Profit_%"
    ]
].copy()

profit_table["Total_Gross_Profit"] = (
    profit_table["Total_Gross_Profit"]
    .round(2)
)

profit_table["Profit_Contribution_%"] = (
    profit_table["Profit_Contribution_%"]
    .round(1)
)

profit_table["Cumulative_Profit_%"] = (
    profit_table["Cumulative_Profit_%"]
    .round(1)
)

st.dataframe(
    profit_table,
    width="stretch",
    hide_index=True
)
# ============================================================
# 5. GEOGRAPHIC / STATE PERFORMANCE
# ============================================================

st.markdown("## 5. Geographic / State Performance")

st.markdown(
    """
    Geographic analysis evaluates sales, cost, gross profit, units,
    and gross margin across states to identify strong markets and
    locations with high sales but relatively weak profitability.
    """
)

# ------------------------------------------------------------
# STATE-LEVEL PERFORMANCE
# ------------------------------------------------------------

state_analysis = filtered_df.groupby(
    "State/Province"
).agg(
    Total_Sales=("Sales", "sum"),
    Total_Cost=("Cost", "sum"),
    Total_Gross_Profit=("Gross Profit", "sum"),
    Total_Units=("Units", "sum")
).reset_index()

state_analysis["Gross_Margin_%"] = (
    state_analysis["Total_Gross_Profit"]
    / state_analysis["Total_Sales"]
) * 100

state_analysis = state_analysis.sort_values(
    "Total_Gross_Profit",
    ascending=False
)

st.markdown("### State-Level Sales and Profitability")

fig_state_profit = px.bar(
    state_analysis.head(15),
    x="State/Province",
    y="Total_Gross_Profit",
    title="Top 15 States by Gross Profit",
    labels={
        "State/Province": "State",
        "Total_Gross_Profit": "Gross Profit"
    }
)

fig_state_profit.update_layout(
    xaxis_tickangle=-45
)

st.plotly_chart(
    fig_state_profit,
    width="stretch"
)

st.dataframe(
    state_analysis,
    width="stretch",
    hide_index=True
)
# ============================================================
# 5.1 HIGH-SALES / LOW-MARGIN STATES
# ============================================================

st.markdown("### High-Sales / Low-Margin States")

# Use the median as the benchmark for identifying
# relatively high-sales and low-margin states
sales_median = state_analysis["Total_Sales"].median()
margin_median = state_analysis["Gross_Margin_%"].median()

high_sales_low_margin = state_analysis[
    (state_analysis["Total_Sales"] >= sales_median) &
    (state_analysis["Gross_Margin_%"] < margin_median)
].copy()

high_sales_low_margin = high_sales_low_margin.sort_values(
    "Total_Sales",
    ascending=False
)

st.markdown(
    """
    These states generate relatively high sales but operate below
    the median gross margin, indicating locations where pricing,
    product mix, or cost structure may require attention.
    """
)

if len(high_sales_low_margin) > 0:

    fig_state_diagnostic = px.scatter(
        state_analysis,
        x="Total_Sales",
        y="Gross_Margin_%",
        size="Total_Gross_Profit",
        hover_name="State/Province",
        title="State Sales vs Gross Margin",
        labels={
            "Total_Sales": "Total Sales",
            "Gross_Margin_%": "Gross Margin (%)"
        }
    )

    fig_state_diagnostic.add_vline(
        x=sales_median,
        line_dash="dash",
        annotation_text="Median Sales"
    )

    fig_state_diagnostic.add_hline(
        y=margin_median,
        line_dash="dash",
        annotation_text="Median Margin"
    )

    st.plotly_chart(
        fig_state_diagnostic,
        width="stretch"
    )

    st.dataframe(
        high_sales_low_margin,
        width="stretch",
        hide_index=True
    )

else:

    st.info(
        "No states currently meet the high-sales / low-margin criteria."
    )


# ============================================================
# 5.2 REGIONAL PROFITABILITY COMPARISON
# ============================================================

st.markdown("### Regional Profitability Comparison")

region_analysis = filtered_df.groupby(
    "Region"
).agg(
    Total_Sales=("Sales", "sum"),
    Total_Cost=("Cost", "sum"),
    Total_Gross_Profit=("Gross Profit", "sum"),
    Total_Units=("Units", "sum")
).reset_index()

region_analysis["Gross_Margin_%"] = (
    region_analysis["Total_Gross_Profit"]
    / region_analysis["Total_Sales"]
) * 100

region_analysis = region_analysis.sort_values(
    "Total_Gross_Profit",
    ascending=False
)

fig_region_profit = px.bar(
    region_analysis,
    x="Region",
    y="Total_Gross_Profit",
    title="Gross Profit by Region",
    labels={
        "Region": "Region",
        "Total_Gross_Profit": "Gross Profit"
    }
)

st.plotly_chart(
    fig_region_profit,
    width="stretch"
)

fig_region_margin = px.bar(
    region_analysis,
    x="Region",
    y="Gross_Margin_%",
    title="Gross Margin by Region",
    labels={
        "Region": "Region",
        "Gross_Margin_%": "Gross Margin (%)"
    }
)

st.plotly_chart(
    fig_region_margin,
    width="stretch"
)

st.dataframe(
    region_analysis,
    width="stretch",
    hide_index=True
)
# ============================================================
# 6. FACTORY PERFORMANCE
# ============================================================

st.markdown("## 6. Factory Performance")

st.markdown(
    """
    Factory-level analysis connects product profitability with the
    manufacturing locations responsible for producing each product.
    This helps identify factories with strong profitability as well
    as locations associated with lower-margin product lines.
    """
)


# ============================================================
# 6.1 PRODUCT-TO-FACTORY MAPPING
# ============================================================

st.markdown("### Product-to-Factory Mapping")

# Product-to-factory mapping based on the analysis dataset

factory_mapping = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory"
}

factory_df = filtered_df.copy()

factory_df["Factory"] = factory_df["Product Name"].map(
    factory_mapping
)

st.dataframe(
    factory_df[
        [
            "Product Name",
            "Factory"
        ]
    ].drop_duplicates().sort_values("Product Name"),
    width="stretch",
    hide_index=True
)


# ============================================================
# 6.2 FACTORY SALES & PROFITABILITY
# ============================================================

st.markdown("### Factory Sales & Profitability")

factory_analysis = factory_df.groupby(
    "Factory"
).agg(
    Total_Sales=("Sales", "sum"),
    Total_Cost=("Cost", "sum"),
    Total_Gross_Profit=("Gross Profit", "sum"),
    Total_Units=("Units", "sum"),
    Product_Count=("Product Name", "nunique")
).reset_index()

factory_analysis["Gross_Margin_%"] = (
    factory_analysis["Total_Gross_Profit"]
    / factory_analysis["Total_Sales"]
) * 100

factory_analysis["Revenue_Contribution_%"] = (
    factory_analysis["Total_Sales"]
    / factory_analysis["Total_Sales"].sum()
) * 100

factory_analysis["Profit_Contribution_%"] = (
    factory_analysis["Total_Gross_Profit"]
    / factory_analysis["Total_Gross_Profit"].sum()
) * 100

factory_analysis = factory_analysis.sort_values(
    "Total_Gross_Profit",
    ascending=False
)


fig_factory_profit = px.bar(
    factory_analysis,
    x="Factory",
    y="Total_Gross_Profit",
    title="Gross Profit by Factory",
    labels={
        "Factory": "Factory",
        "Total_Gross_Profit": "Gross Profit"
    }
)

st.plotly_chart(
    fig_factory_profit,
    width="stretch"
)


# ============================================================
# 6.3 FACTORY MARGIN COMPARISON
# ============================================================

st.markdown("### Factory Margin Comparison")

fig_factory_margin = px.bar(
    factory_analysis,
    x="Factory",
    y="Gross_Margin_%",
    title="Gross Margin by Factory",
    labels={
        "Factory": "Factory",
        "Gross_Margin_%": "Gross Margin (%)"
    },
    text="Gross_Margin_%"
)

fig_factory_margin.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="outside"
)

st.plotly_chart(
    fig_factory_margin,
    width="stretch"
)


st.dataframe(
    factory_analysis[
        [
            "Factory",
            "Total_Sales",
            "Total_Cost",
            "Total_Gross_Profit",
            "Total_Units",
            "Product_Count",
            "Gross_Margin_%",
            "Revenue_Contribution_%",
            "Profit_Contribution_%"
        ]
    ].round(2),
    width="stretch",
    hide_index=True
)


# ============================================================
# 6.4 FACTORY LOCATIONS
# ============================================================

st.markdown("### Factory Locations")

factory_locations = pd.DataFrame({
    "Factory": [
        "Lot's O' Nuts",
        "Wicked Choccy's",
        "Sugar Shack",
        "Secret Factory",
        "The Other Factory"
    ],
    "Latitude": [
        32.881893,
        32.076176,
        48.11914,
        41.446333,
        35.1175
    ],
    "Longitude": [
        -111.768036,
        -81.088371,
        -96.18115,
        -90.565487,
        -89.971107
    ]
})

factory_locations_filtered = factory_locations[
    factory_locations["Factory"].isin(
        factory_analysis["Factory"]
    )
].copy()

st.map(
    factory_locations_filtered,
    latitude="Latitude",
    longitude="Longitude"
)

st.dataframe(
    factory_locations_filtered,
    width="stretch",
    hide_index=True
)
# ============================================================
# 7. KEY MANAGEMENT INSIGHTS
# ============================================================

st.markdown("## 7. Key Management Insights")

st.markdown(
    """
    The following insights summarize the main profitability,
    concentration, geographic, and operational patterns identified
    in the filtered dataset.
    """
)

# ------------------------------------------------------------
# INSIGHT 1 — OVERALL PROFITABILITY
# ------------------------------------------------------------

total_revenue = filtered_df["Sales"].sum()
total_profit = filtered_df["Gross Profit"].sum()

overall_margin = (
    total_profit / total_revenue * 100
    if total_revenue != 0 else 0
)

st.markdown("### Overall Profitability")

st.write(
    f"""
    The selected dataset generates total revenue of
    **${total_revenue:,.0f}** and gross profit of
    **${total_profit:,.0f}**, resulting in an overall gross margin
    of approximately **{overall_margin:.1f}%**.
    """
)


# ------------------------------------------------------------
# INSIGHT 2 — TOP PROFITABLE DIVISION
# ------------------------------------------------------------

division_insights = filtered_df.groupby(
    "Division"
).agg(
    Sales=("Sales", "sum"),
    Gross_Profit=("Gross Profit", "sum")
).reset_index()

division_insights["Gross_Margin_%"] = (
    division_insights["Gross_Profit"]
    / division_insights["Sales"]
) * 100

top_division = division_insights.loc[
    division_insights["Gross_Profit"].idxmax()
]

st.markdown("### Division Performance")

st.write(
    f"""
    **{top_division['Division']}** is the strongest division by gross
    profit, generating approximately **${top_division['Gross_Profit']:,.0f}**
    in gross profit with a gross margin of
    **{top_division['Gross_Margin_%']:.1f}%**.
    """
)


# ------------------------------------------------------------
# INSIGHT 3 — TOP PROFIT PRODUCTS
# ------------------------------------------------------------

product_insights = filtered_df.groupby(
    "Product Name"
).agg(
    Sales=("Sales", "sum"),
    Gross_Profit=("Gross Profit", "sum")
).reset_index()

product_insights["Gross_Margin_%"] = (
    product_insights["Gross_Profit"]
    / product_insights["Sales"]
) * 100

top_product = product_insights.loc[
    product_insights["Gross_Profit"].idxmax()
]

st.markdown("### Product Profitability")

st.write(
    f"""
    The highest gross-profit product is
    **{top_product['Product Name']}**, generating approximately
    **${top_product['Gross_Profit']:,.0f}** in gross profit with a
    gross margin of **{top_product['Gross_Margin_%']:.1f}%**.
    """
)


# ------------------------------------------------------------
# INSIGHT 4 — LOWEST-MARGIN PRODUCT
# ------------------------------------------------------------

lowest_margin_product = product_insights.loc[
    product_insights["Gross_Margin_%"].idxmin()
]

st.markdown("### Low-Margin Product Risk")

st.write(
    f"""
    **{lowest_margin_product['Product Name']}** has the lowest gross
    margin at approximately **{lowest_margin_product['Gross_Margin_%']:.1f}%**.
    This product should be reviewed for pricing, cost structure,
    supplier costs, or product-level strategic viability.
    """
)


# ------------------------------------------------------------
# INSIGHT 5 — PROFIT CONCENTRATION
# ------------------------------------------------------------

profit_concentration = product_insights.sort_values(
    "Gross_Profit",
    ascending=False
).reset_index(drop=True)

profit_concentration["Cumulative_Profit_%"] = (
    profit_concentration["Gross_Profit"].cumsum()
    / profit_concentration["Gross_Profit"].sum()
) * 100

products_for_80_profit = (
    profit_concentration[
        profit_concentration["Cumulative_Profit_%"] >= 80
    ].index[0] + 1
)

total_products = len(profit_concentration)

st.markdown("### Profit Concentration")

st.write(
    f"""
    Only **{products_for_80_profit} out of {total_products} products**
    are required to generate at least 80% of gross profit. This indicates
    that profitability is concentrated among a relatively small number
    of products and that dependency on key products should be monitored.
    """
)


# ------------------------------------------------------------
# INSIGHT 6 — FACTORY PERFORMANCE
# ------------------------------------------------------------

factory_insights = filtered_df.copy()

factory_insights["Factory"] = factory_insights[
    "Product Name"
].map(factory_mapping)

factory_summary = factory_insights.groupby(
    "Factory"
).agg(
    Sales=("Sales", "sum"),
    Gross_Profit=("Gross Profit", "sum")
).reset_index()

factory_summary["Gross_Margin_%"] = (
    factory_summary["Gross_Profit"]
    / factory_summary["Sales"]
) * 100

best_factory = factory_summary.loc[
    factory_summary["Gross_Profit"].idxmax()
]

st.markdown("### Factory Performance")

st.write(
    f"""
    **{best_factory['Factory']}** is currently the strongest factory
    by gross profit, generating approximately
    **${best_factory['Gross_Profit']:,.0f}** with a gross margin of
    **{best_factory['Gross_Margin_%']:.1f}%**.
    """
)


# ------------------------------------------------------------
# MANAGEMENT RECOMMENDATIONS
# ------------------------------------------------------------

st.markdown("### Management Recommendations")

st.markdown(
    """
    **1. Protect high-profit products**  
    Prioritize products that contribute strongly to gross profit and
    maintain healthy margins.

    **2. Review low-margin products**  
    Products with weak margins should be evaluated for repricing,
    cost reduction, supplier renegotiation, or strategic
    discontinuation.

    **3. Monitor profit concentration**  
    Heavy dependence on a small number of products creates
    concentration risk. Expanding profitable product categories
    can improve resilience.

    **4. Investigate geographic differences**  
    High-sales but low-margin states should be reviewed for pricing,
    product mix, distribution costs, and market-specific conditions.

    **5. Use factory performance for operational decisions**  
    Factory-level profitability can support decisions related to
    production planning, cost management, and product allocation.
    """
)