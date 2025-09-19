# retail_dashboard.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(page_title="Retail Insights Dashboard", layout="wide")
st.title("Retail Insights Dashboard")
st.markdown("*Unlocking sales performance and customer behavior with actionable analytics*")

# Professional seaborn style
sns.set(style="whitegrid", palette="pastel")

# -----------------------------
# Sidebar - Filters
# -----------------------------
st.sidebar.header("Filters")
uploaded_file = st.sidebar.file_uploader("Upload dataset (Excel/CSV)", type=["xlsx","csv"])

if uploaded_file is not None:
    # -----------------------------
    # Load Data
    # -----------------------------
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
    st.success("Dataset loaded successfully!")

    # -----------------------------
    # Data Cleaning
    # -----------------------------
    df["Total_Amount"] = df["Quantity"] * df["Price"]
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('-', '_')
    df = df.dropna(subset=['Customer_ID','InvoiceDate'])
    df = df[df['Total_Amount'] > 0]
    if df['Invoice'].dtype == object:
        df = df[~df['Invoice'].astype(str).str.startswith('C')]
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df = df.drop_duplicates()

    # -----------------------------
    # Filters
    # -----------------------------
    country_list = ['All'] + sorted(df['Country'].unique().tolist())
    selected_country = st.sidebar.selectbox("Select Country", country_list)
    if selected_country != 'All':
        df = df[df['Country'] == selected_country]

    # -----------------------------
    # KPIs
    # -----------------------------
    col1, col2, col3 = st.columns(3)
    total_revenue = df['Total_Amount'].sum()
    total_customers = df['Customer_ID'].nunique()
    avg_basket = df.groupby('Invoice')['Total_Amount'].sum().mean()

    col1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
    col2.metric("Total Customers", total_customers)
    col3.metric("Avg Basket Size", f"₹{avg_basket:.2f}")

    # -----------------------------
    # EDA
    # -----------------------------
    st.header("Exploratory Data Analysis")

    # Top 10 Products
    st.subheader("Top 10 Best-Selling Products")
    top_products = df.groupby("Description")['Total_Amount'].sum().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(12,6))
    sns.barplot(x=top_products.values, y=top_products.index, palette="Blues_d", ax=ax)
    ax.set_xlabel("Total Sales Amount")
    ax.set_ylabel("Product Description")
    ax.set_title("Top 10 Best Selling Products")
    st.pyplot(fig)

    # Monthly Sales
    st.subheader("Monthly Sales Trend")
    df["YearMonth"] = df["InvoiceDate"].dt.to_period("M")
    monthly_sales = df.groupby("YearMonth")['Total_Amount'].sum()
    fig, ax = plt.subplots(figsize=(12,5))
    sns.lineplot(x=monthly_sales.index.astype(str), y=monthly_sales.values, marker="o", color="#1f77b4", ax=ax)
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Sales")
    ax.set_title("Monthly Sales Trend")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # Top Customers
    st.subheader("Top 10 Customers by Spend")
    top_customers = df.groupby("Customer_ID")['Total_Amount'].sum().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(12,5))
    sns.barplot(x=top_customers.values, y=top_customers.index, palette="Greens_d", ax=ax)
    ax.set_xlabel("Total Spend")
    ax.set_ylabel("Customer ID")
    ax.set_title("Top 10 Customers by Spend")
    st.pyplot(fig)

    # Revenue by Country
    st.subheader("Top 10 Countries by Revenue")
    revenue_country = df.groupby("Country")['Total_Amount'].sum().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(10,6))
    sns.barplot(x=revenue_country.values, y=revenue_country.index, palette="Oranges_d", ax=ax)
    ax.set_xlabel("Total Revenue")
    ax.set_ylabel("Country")
    ax.set_title("Top Countries by Revenue")
    st.pyplot(fig)

    # -----------------------------
    # RFM Analysis
    # -----------------------------
    st.header("Customer Segmentation (RFM Analysis)")

    # Recency
    df_recency = df.groupby('Customer_ID', as_index=False)['InvoiceDate'].max()
    df_recency.columns = ['Customer_ID','LastPurchaseDate']
    most_recent_date = df_recency['LastPurchaseDate'].max()
    df_recency['Recency'] = (most_recent_date - df_recency['LastPurchaseDate']).dt.days

    # Frequency
    df_frequency = df.groupby('Customer_ID', as_index=False)['Invoice'].nunique()
    df_frequency.columns = ['Customer_ID','Frequency']

    # Monetary
    df_monetary = df.groupby('Customer_ID', as_index=False)['Total_Amount'].sum()
    df_monetary.columns = ['Customer_ID','Monetary']

    # Combine RFM
    RFM = df_recency.merge(df_frequency, on='Customer_ID').merge(df_monetary, on='Customer_ID')

    # Scoring
    RFM['R_Score'] = pd.qcut(RFM['Recency'], 5, labels=[5,4,3,2,1])
    RFM['F_Score'] = pd.qcut(RFM['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])
    RFM['M_Score'] = pd.qcut(RFM['Monetary'], 5, labels=[1,2,3,4,5])
    RFM['RFM_Score'] = RFM['R_Score'].astype(str) + RFM['F_Score'].astype(str) + RFM['M_Score'].astype(str)

    # Segmentation
    def segment(score):
        if score == "555":
            return "Champions"
        elif score.startswith("5") or score.startswith("4"):
            return "Loyal"
        elif score.startswith("1"):
            return "Lost"
        else:
            return "Others"
    RFM["Segment"] = RFM["RFM_Score"].apply(segment)

    # Show RFM Table
    st.subheader("RFM Sample Table")
    st.dataframe(RFM.head(10))

    # Segment Distribution - Pie Chart
    st.subheader("Customer Segment Distribution (Pie Chart)")
    segment_counts = RFM["Segment"].value_counts()
    fig, ax = plt.subplots(figsize=(6,6))
    colors = sns.color_palette("Set2", len(segment_counts))
    ax.pie(segment_counts, labels=segment_counts.index, autopct="%1.1f%%", startangle=140, colors=colors)
    st.pyplot(fig)

    # RFM Segment Metrics
    st.subheader("RFM Segment Metrics")
    revenue_per_segment = RFM.groupby('Segment')['Monetary'].sum()
    avg_monetary_segment = RFM.groupby('Segment')['Monetary'].mean()
    col1, col2, col3 = st.columns(3)
    col1.metric("Largest Segment", segment_counts.idxmax())
    col2.metric("Highest Revenue Segment", revenue_per_segment.idxmax())
    col3.metric(
    "Highest Avg Spend Segment",
    value=f"{avg_monetary_segment.idxmax()} (₹{avg_monetary_segment.max():,.2f})"
)

   


    # Segment Distribution - Bar Chart
    st.subheader("Customer Segment Distribution - Bar Chart")
    fig, ax = plt.subplots(figsize=(8,5))
    sns.barplot(x=segment_counts.index, y=segment_counts.values, palette="pastel", ax=ax)
    ax.set_xlabel("Segment")
    ax.set_ylabel("Number of Customers")
    ax.set_title("Number of Customers per Segment")
    st.pyplot(fig)

    # Top Champions Customers
    st.subheader("Top Customers in Champions Segment")
    top_champions = RFM[RFM['Segment']=='Champions'].sort_values(by='Monetary', ascending=False).head(5)
    st.dataframe(top_champions[['Customer_ID','Monetary','Frequency','Recency']])

    # Download RFM Table
    st.download_button(
        label="Download Full RFM Data",
        data=RFM.to_csv(index=False).encode(),
        file_name="RFM_segmented_customers.csv",
        mime="text/csv"
    )
