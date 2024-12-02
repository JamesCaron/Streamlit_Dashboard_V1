import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import timedelta
from matplotlib.ticker import FuncFormatter

# Apply custom theme using markdown and CSS
st.markdown(
    """
    <style>
    body {
        background-color: #0f173a;
        color: #f3f3f4;
    }
    .css-1offfwp {
        background-color: #0f173a;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #f3f3f4;
    }
    .stButton button {
        background-color: #18a1f6;
        color: white;
        border-radius: 5px;
    }
    .stButton button:hover {
        background-color: #bb43a7;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Streamlit app
st.title("E-Commerce Dashboard")

# Load the data directly
data_path = r'C:\Users\james\Documents\Data Projects\Streamlit hello world\ecommerce_data_updated.csv'
df = pd.read_csv(data_path)

# Convert `Date` column to datetime and then to date
df["Date"] = pd.to_datetime(df["Date"]).dt.date

# Standardize column names
df.columns = (
    df.columns.str.replace(" ", "_")
    .str.replace("(", "", regex=False)
    .str.replace(")", "", regex=False)
    .str.replace("%", "Percent", regex=False)
    .str.replace("/", "_", regex=False)
)

# Formatting the display values
def format_value(value, metric):
    if metric in ["Total Sales", "Ad Spend", "Profit"]:
        if value >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"  # Abbreviate millions
        elif value >= 1_000:
            return f"${value / 1_000:.2f}K"  # Abbreviate thousands
        else:
            return f"${value:,.2f}"  # Full number with commas
    elif metric == "Units Sold":
        return f"{int(value):,}"  # Integer formatting
    else:
        return f"{value:.2f}%"  # Percentage

# Sidebar: Date Range Selection Dropdown
st.sidebar.header("Filters")
time_range = st.sidebar.selectbox(
    "Select Time Range",
    options=["Last 30 Days", "Last 7 Days"],
    index=0  # Default to Last 30 Days
)

# Determine the latest date in the dataset
latest_date = df["Date"].max()

# Filter the dataset for the selected time range
if time_range == "Last 30 Days":
    filtered_df = df[df["Date"] > (latest_date - timedelta(days=30))]
    comparison_period = "30 Days"
elif time_range == "Last 7 Days":
    filtered_df = df[df["Date"] > (latest_date - timedelta(days=7))]
    comparison_period = "7 Days"

# Calculate the start and end dates for the comparison period
if time_range == "Last 30 Days":
    start_date = latest_date - timedelta(days=60)
    end_date = latest_date - timedelta(days=30)
elif time_range == "Last 7 Days":
    start_date = latest_date - timedelta(days=14)
    end_date = latest_date - timedelta(days=7)

# Filter the dataset for the previous period
previous_period_df = df[(df["Date"] >= start_date) & (df["Date"] < end_date)]

# Calculate account metrics for the selected period
account_metrics = {
    "Total Sales": filtered_df["Total_Sales_USD"].sum() if "Total_Sales_USD" in filtered_df else 0,
    "Units Sold": filtered_df["Total_Units_Sold"].sum() if "Total_Units_Sold" in filtered_df else 0,
    "Profit": filtered_df["Profit_USD"].sum() if "Profit_USD" in filtered_df else 0,
    "Profit Margin": round((filtered_df["Profit_USD"].sum() / filtered_df["Total_Sales_USD"].sum()) * 100, 2)
    if "Total_Sales_USD" in filtered_df and filtered_df["Total_Sales_USD"].sum() > 0 else 0,
    "Ad Spend": filtered_df["Ad_Spend_USD"].sum() if "Ad_Spend_USD" in filtered_df else 0,
    "TACOS": round(filtered_df["TACOS_Percent"].mean(), 2) if "TACOS_Percent" in filtered_df else 0,
    "% of Sales from Ads": round(filtered_df["Percent_of_Sales_from_Ads"].mean(), 2)
    if "Percent_of_Sales_from_Ads" in filtered_df else 0,
    "ACOS": round(filtered_df["ACOS_Percent"].mean(), 2) if "ACOS_Percent" in filtered_df else 0,
}

# Calculate percentage changes for the selected time range
changes = {}
for metric, value in account_metrics.items():
    col_name = metric.replace(" ", "_").replace("%", "Percent")
    if col_name and col_name in previous_period_df.columns:
        prev_value = previous_period_df[col_name].sum()
        if prev_value > 0:
            changes[metric] = round(((value - prev_value) / prev_value) * 100, 2)
        else:
            changes[metric] = 0  # Avoid division by zero
    else:
        changes[metric] = 0  # If column is missing, default to 0%

# Display account metrics with percentage changes
st.subheader(f"Account Metrics for the Last {comparison_period}")
metrics = list(account_metrics.items())
for i in range(0, len(metrics), 4):  # Keep 4 columns per row
    cols = st.columns(4)
    for col, (metric, value) in zip(cols, metrics[i:i+4]):
        delta_color = "inverse" if metric in ["TACOS", "% of Sales from Ads", "ACOS"] else "normal"
        display_value = format_value(value, metric)
        change = changes.get(metric, 0)
        change_text = f"{change:+}%" if change != 0 else "0%"
        col.metric(metric, display_value, change_text, delta_color=delta_color)

# Dropdown for SKU selection (one selection box for both graph and table)
selected_sku = st.selectbox("Select SKU", filtered_df["SKU"].unique())

if selected_sku:
    sku_data = filtered_df[filtered_df["SKU"] == selected_sku]

    # Calculate a 7-day rolling average for Profit Margin
    sku_data["Profit_Margin_Percent"] = sku_data["Profit_Margin_Percent"].fillna(0)  # Fill missing values
    sku_data["Profit_Margin_Percent_Rolling"] = sku_data["Profit_Margin_Percent"].rolling(7, min_periods=1).mean()

    # Plot the graph
    st.subheader(f"Units Sold, Sales, Profit & Margin for {selected_sku}")
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar chart: Units Sold
    ax1.bar(
        sku_data["Date"], 
        sku_data["Total_Units_Sold"], 
        label="Units Sold", 
        color="#1f77b4",  # Light blue
        alpha=0.6
    )
    ax1.set_ylabel("Units Sold", color="#1f77b4")
    ax1.set_xlabel("Date", color="#FFFFFF")  # Set x-axis label color
    ax1.tick_params(axis="y", labelcolor="#1f77b4")
    ax1.tick_params(axis="x", labelcolor="#FFFFFF")  # Set x-axis tick color

    # Line charts: Total Sales and Profit (on primary Y-axis)
    ax2 = ax1.twinx()
    ax2.plot(
        sku_data["Date"], 
        sku_data["Total_Sales_USD"], 
        label="Total Sales", 
        color="#ff7f0e",  # Orange
        linewidth=2
    )
    ax2.plot(
        sku_data["Date"], 
        sku_data["Profit_USD"], 
        label="Profit", 
        color="#2ca02c",  # Green
        linewidth=2
    )
    ax2.set_ylabel("Sales and Profit (USD)", color="#ff7f0e")  # Set y-axis label color
    ax2.tick_params(axis="y", labelcolor="#ff7f0e")

    # Third Y-axis for Profit Margin Percent (7-day rolling average)
    ax3 = ax1.twinx()
    ax3.spines["right"].set_position(("outward", 60))  # Offset third y-axis
    ax3.plot(
        sku_data["Date"], 
        sku_data["Profit_Margin_Percent_Rolling"], 
        label="7D Avg Profit Margin (%)", 
        color="#9467bd",  # Purple
        linewidth=2, 
        linestyle="dashed"
    )
    ax3.set_ylabel("7D Avg Profit Margin (%)", color="#9467bd")  # Set y-axis label color
    ax3.tick_params(axis="y", labelcolor="#9467bd")

    # Title with adjusted color and position
    plt.title(
        f"Sales and Profit Metrics for {selected_sku} (with 7-day Avg Margin %)", 
        fontsize=14, 
        color="#000000",  # Set title color to black
        y=1.05  # Adjust title position slightly upward
    )

    # Formatter for percentage values
    def percent_format(x, _):
        return f"{x:.0f}%"

    ax3.yaxis.set_major_formatter(FuncFormatter(percent_format))

    # Add legends at the bottom
    fig.legend(
        loc="lower center",  # Position legend at the bottom
        bbox_to_anchor=(0.5, -0.2),  # Adjust to center below the graph
        ncol=3,  # Arrange items in 3 columns
        fontsize=10,
        frameon=False  # Remove legend frame for a clean look
    )

    # Ensure spacing between elements
    plt.tight_layout()

    # Render the plot
    st.pyplot(fig)


# SKU Details Table
st.subheader(f"Details for {selected_sku}")
seo_data = filtered_df[filtered_df["SKU"] == selected_sku]

# Commented out SEO Score display for now
# st.write(f"SEO Score for {selected_sku}: {seo_data['SEO_Score'].mean():.2f}")
st.write(seo_data)
