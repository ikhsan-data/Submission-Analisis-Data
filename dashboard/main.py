import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import matplotlib.image as mpimg
import urllib.request

sns.set(style='dark')

datetime_cols = ["order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date", "order_purchase_timestamp", "shipping_limit_date"]

# Load Data (outside the class)
try:
    all_df = pd.read_csv('all_data.csv')
    geolocation_customer = pd.read_csv('geolocation_customer.csv')
    geolocation_seller = pd.read_csv('geolocation_seller.csv')
except FileNotFoundError as e:
    st.error(f"File not found: {e}")
    st.stop()
except pd.errors.ParserError as e:
    st.error(f"Error parsing CSV: {e}")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
    st.stop()

all_df.sort_values(by="order_approved_at", inplace=True)
all_df.reset_index(inplace=True, drop=True)

for col in datetime_cols:
    if col in all_df.columns: 
        all_df[col] = pd.to_datetime(all_df[col])

# Data Analyzer Class
class DataAnalyzer:
    def __init__(self, df):
        self.df = df.copy()
        if 'order_approved_at' in self.df.columns:
            self.df['order_date'] = self.df['order_approved_at'].dt.to_period('D')
        if 'total_price' not in self.df.columns and 'price' in self.df.columns and 'order_item_id' in self.df.columns:
            self.df['total_price'] = self.df['price'] * self.df['order_item_id']

    def create_daily_orders_df(self):
        if 'order_approved_at' not in self.df.columns or self.df.empty:
            return pd.DataFrame()

        daily_orders_df = self.df.resample(rule='D', on='order_approved_at').agg({
            "order_id": "nunique",
            "total_price": "sum"
        })
        daily_orders_df = daily_orders_df.reset_index()
        daily_orders_df.rename(columns={
            "order_id": "order_count",
            "total_price": "revenue",
            "order_approved_at": "order_date" # Memastikan kolom order_date ada
        }, inplace=True)
        return daily_orders_df
    
    def create_sum_order_items_df(self):
        if 'product_category_name_english' in self.df.columns:
            sum_order_items_df = self.df.groupby('product_category_name_english')['order_id'].count().reset_index()
            sum_order_items_df = sum_order_items_df.rename(columns={'order_id': 'product_count'})
            sum_order_items_df = sum_order_items_df.sort_values(by='product_count', ascending=False)
            return sum_order_items_df
        else:
            return pd.DataFrame()
        
    
    def create_payment_type_df(self):
        if 'payment_type' not in self.df.columns or self.df.empty:
            return pd.DataFrame()

        payment_type_df = self.df['payment_type'].value_counts().reset_index()
        payment_type_df.columns = ['payment_type', 'count']
        return payment_type_df


    def create_bystate_df(self):
        bystate_df = self.df.groupby(by="customer_state").customer_id.nunique().reset_index()
        bystate_df.rename(columns={
            "customer_id": "customer_count"
        }, inplace=True)
        most_common_state = bystate_df.loc[bystate_df['customer_count'].idxmax(), 'customer_state']
        bystate_df = bystate_df.sort_values(by='customer_count', ascending=False)

        return bystate_df, most_common_state
    
    def create_customer_bystate_df(self):
        customer_bystate_df = self.df.groupby(by="customer_state").customer_id.nunique().reset_index()
        customer_bystate_df.rename(columns={
            "customer_id": "customer_count"
        }, inplace=True)
        most_common_state = customer_bystate_df.loc[customer_bystate_df['customer_count'].idxmax(), 'customer_state']
        customer_bystate_df = customer_bystate_df.sort_values(by='customer_count', ascending=False)

        return customer_bystate_df, most_common_state
    
        
    def create_seller_bystate_df(self):
        seller_bystate_df = self.df.groupby(by="seller_state").seller_id.nunique().reset_index()
        seller_bystate_df.rename(columns={
            "seller_id": "seller_count"
        }, inplace=True)
        most_common_state = seller_bystate_df.loc[seller_bystate_df['seller_count'].idxmax(), 'seller_state']
        seller_bystate_df = seller_bystate_df.sort_values(by='seller_count', ascending=False)

        return seller_bystate_df, most_common_state
    
    def create_seller_product_count_df(self, df): # Menerima df sebagai argumen
        if df.empty or 'seller_id' not in df.columns or 'product_id' not in df.columns:
            return pd.DataFrame()
        seller_product_counts = df.groupby('seller_id')['product_id'].count().reset_index()
        seller_product_counts.rename(columns={'product_id': 'product_count'}, inplace=True)
        seller_product_counts = seller_product_counts.sort_values(by='product_count', ascending=False)
        return seller_product_counts
        


def plot_brazil_map(ax, data, title="Distribusi di Brazil", color="", figsize=(12, 12)):
    try:
        brazil = mpimg.imread(
            urllib.request.urlopen(
                'https://i.pinimg.com/originals/3a/0c/e1/3a0ce18b3c842748c255bc0aa445ad41.jpg'
            ),
            'jpg'
        )
    except urllib.error.URLError:
        st.error("Gagal mengunduh gambar peta Brazil. Periksa koneksi internet Anda.")
        return

    ax.imshow(brazil, extent=[-73.98283055, -33.8, -33.75116944, 5.4], aspect='auto')
    if data.empty:
        st.warning(f"Tidak ada data untuk ditampilkan pada peta: {title}") 
        return
    
    data.plot(
        kind="scatter",
        x="geolocation_lng",
        y="geolocation_lat",
        alpha=0.3,
        s=2,  # Sedikit diperbesar
        c=color,
        ax=ax
    )
    ax.set_title(title, fontsize=16)
    ax.axis('off')

class BrazilMapPlotter:
    def __init__(self, plt, mpimg, urllib, st):
        self.plt = plt
        self.mpimg = mpimg
        self.urllib = urllib
        self.st = st
        
    

    def plot_customer(self, data, title="Persebaran Customer di Brazil"):
        fig, ax = self.plt.subplots(figsize=(12, 12))
        plot_brazil_map(ax, data, title, 'blue', figsize=(12, 12))
        self.plt.tight_layout()
        self.st.pyplot(fig)

    def plot_seller(self, data, title="Persebaran Penjual di Brazil"):
        fig, ax = self.plt.subplots(figsize=(12, 12))
        plot_brazil_map(ax, data, title, 'green', figsize=(12, 12))
        self.plt.tight_layout()
        self.st.pyplot(fig)
        
# Streamlit App
min_date = all_df["order_approved_at"].min()
max_date = all_df["order_approved_at"].max()

with st.sidebar:
    # Title
    st.title("Ikhsan Aditya N. Q.")

    # Logo Image
    st.image("gcl.png")

    # Date Range
    start_date, end_date = st.date_input(
        label="Select Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )


main_df = all_df[(all_df["order_approved_at"] >= pd.to_datetime(start_date)) & (all_df["order_approved_at"] <= pd.to_datetime(end_date))] if 'order_approved_at' in all_df else all_df

function = DataAnalyzer(main_df)
map_plotter = BrazilMapPlotter(plt=plt, mpimg=mpimg, urllib=urllib, st=st)

daily_orders_df = function.create_daily_orders_df()

sum_order_items_df = function.create_sum_order_items_df()
print(sum_order_items_df)

payment_type_df = function.create_payment_type_df()

customer_bystate_df, most_common_state = function.create_customer_bystate_df()

seller_bystate_df, most_common_state = function.create_seller_bystate_df()

order_item_df = main_df[['order_id', 'order_item_id', 'product_id', 'seller_id']] if 'seller_id' in main_df and 'product_id' in main_df else pd.DataFrame()
seller_df = main_df[['seller_id', 'seller_zip_code_prefix', 'seller_state', 'seller_city']].drop_duplicates(subset='seller_id') if 'seller_id' in main_df else pd.DataFrame()
top_sellers = function.create_seller_product_count_df(order_item_df).head(10)
if not top_sellers.empty and not seller_df.empty:
    top_sellers = pd.merge(top_sellers, seller_df, on='seller_id', how='left')

st.header("Dashboard E-Commerce :convenience_store:")

# 1. Performa dan Revenue Bulanan
st.subheader("Performa dan Revenue Bulanan")
if not daily_orders_df.empty:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(daily_orders_df["order_date"], daily_orders_df["order_count"], label="Jumlah Order") # Plot langsung dengan order_date
    ax.plot(daily_orders_df["order_date"], daily_orders_df["revenue"], label="Revenue") # Plot langsung dengan order_date
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Jumlah/Revenue")
    ax.set_title("Performa dan Revenue Harian")
    ax.legend()
    st.pyplot(fig)
else:
    st.write("No data available for the selected date range.")

# 2. Produk Terlaris dan Kurang Laris
st.subheader("Produk Terlaris dan Kurang Laris")
if not sum_order_items_df.empty:
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20, 6))

    # Grafik Top 5 Produk
    top_5_products = sum_order_items_df.head(5)
    sns.barplot(x="product_count", y="product_category_name_english", hue="product_count", data=top_5_products, palette='Blues', ax=ax[0])
    ax[0].set_ylabel(None)
    ax[0].set_xlabel("Product Count")
    ax[0].set_title("Products with the Highest Sales", loc="center", fontsize=20)
    ax[0].tick_params(axis='y', labelsize=16)

    # Grafik Bottom 5 Produk
    bottom_5_products = sum_order_items_df.tail(5)
    bottom_5_products = bottom_5_products.sort_values('product_count', ascending=True)
    sns.barplot(x="product_count", y="product_category_name_english", hue="product_count", data=bottom_5_products, palette='Reds', ax=ax[1])
    ax[1].set_ylabel(None)
    ax[1].set_xlabel("Product Count")
    ax[1].invert_xaxis()
    ax[1].yaxis.set_label_position("right")
    ax[1].yaxis.tick_right()
    ax[1].set_title("Products with the Lowest Sales", loc="center", fontsize=20)
    ax[1].tick_params(axis='y', labelsize=16)

    # Menyesuaikan tata letak
    plt.tight_layout()

    # Display charts using Streamlit
    st.pyplot(fig)
else:
    st.write("No data available to display product categories.")

# Menyesuaikan tata letak
plt.tight_layout()
plt.show()


# 3. Metode Pembayaran
st.subheader("Metode Pembayaran")

if not payment_type_df.empty:
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = sns.color_palette("Set3", len(payment_type_df))

    wedges, texts, autotexts = ax.pie(
        payment_type_df['count'],
        labels=payment_type_df['payment_type'],
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        labeldistance=1.1,
        pctdistance=0.85
    )

    ax.set_title('Penggunaan Metode Pembayaran', fontsize=14)
    ax.axis('equal')

    plt.setp(autotexts, size=10, weight="bold", color="black")

    st.pyplot(fig)
else:
    st.write("Informasi pembayaran tidak tersedia.")


# 4. Persebaran Pelanggan
st.subheader("Persebaran Pelanggan Berdasarkan Lokasi")
if 'customer_state' in all_df.columns and not geolocation_customer.empty: # Memastikan kolom dan dataframe ada
    geolocation_customer['geolocation_zip_code_prefix'] = geolocation_customer['geolocation_zip_code_prefix'].astype(str)
    main_df['customer_zip_code_prefix'] = main_df['customer_zip_code_prefix'].astype(str)

    customer_geolocation = geolocation_customer.drop_duplicates(subset='customer_id') # Menghapus duplikat customer_id

    # Menampilkan peta persebaran pelanggan
    map_plotter.plot_customer(customer_geolocation, title="Persebaran Pelanggan di Brazil")
else:
    st.write("Customer state information is not available.")

# 5. Persebaran Penjual  
st.subheader("Persebaran Penjual Berdasarkan Lokasi")
if 'seller_state' in all_df.columns and not geolocation_seller.empty: # Memastikan kolom dan dataframe ada
    geolocation_seller['geolocation_zip_code_prefix'] = geolocation_seller['geolocation_zip_code_prefix'].astype(str)
    main_df['seller_zip_code_prefix'] = main_df['seller_zip_code_prefix'].astype(str)

    seller_geolocation = geolocation_seller.drop_duplicates(subset='seller_id')  # Menghapus duplikat seller_id

    # Menampilkan peta persebaran penjual 
    map_plotter.plot_seller(seller_geolocation, title="Persebaran Penjual di Brazil")
else:
    st.write("Seller state information is not available.")
    

# 6. Top Seller
st.subheader("Top Sellers by Penjualan")

if not top_sellers.empty:
    # Mengurutkan DataFrame berdasarkan product_count
    top_sellers = top_sellers.sort_values('product_count', ascending=False)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Membuat gradasi warna
    n_colors = len(top_sellers)
    colors = sns.color_palette("Greens", n_colors)

    ax = sns.barplot(x="product_count", y="seller_id", hue="product_count", data=top_sellers, palette=colors, ax=ax, orient='h')

    ax.set_xlabel("Jumlah Produk")
    ax.set_ylabel("ID Penjual")
    ax.set_title("Top Penjual Berdasarkan Jumlah Produk")


    plt.tight_layout()
    st.pyplot(fig)
else:
    st.write("No seller data available.")