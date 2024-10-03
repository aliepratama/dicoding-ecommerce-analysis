import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os
import geopandas as gpd

CURRENT_DIR = os.path.join(os.path.abspath(os.curdir), 'data')

def cleaning(df):
    df.dropna(inplace=True)
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['order_approved_at'] = pd.to_datetime(df['order_approved_at'])
    df['order_delivered_carrier_date'] = pd.to_datetime(df['order_delivered_carrier_date'])
    df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'])
    df['order_estimated_delivery_date'] = pd.to_datetime(df['order_estimated_delivery_date'])

def grouping_geo(df_geo, df_customer):
    return df_customer.join(
        df_geo.set_index('geolocation_zip_code_prefix'), 
        on='customer_zip_code_prefix',        
        how='inner').groupby(
            by='customer_city').agg(
                jumlah=pd.NamedAgg(
                    column='customer_city', 
                    aggfunc='count'),
                lat=pd.NamedAgg(
                    column='geolocation_lat', 
                    aggfunc='first'),
                lng=pd.NamedAgg(
                    column='geolocation_lng', 
                    aggfunc='first')).sort_values(
                        by='jumlah', 
                        ascending=False).reset_index()

def grouping_payment(df_payment):
    return df_payment.groupby(
        by='payment_type').agg(
            jumlah=pd.NamedAgg(
                column='payment_type', 
                aggfunc='count')).sort_values(
                    by='jumlah', 
                    ascending=False).reset_index()

def grouping_status(df_order):
    return df_order.groupby(
        by='order_status'
        ).agg(
            jumlah=pd.NamedAgg(
                column='order_status', 
                aggfunc='count')).sort_values(
                    by='jumlah',
                    ascending=False).reset_index()

def grouping_trend(df_order, df_payment):
    return df_order.join(
        df_payment.set_index('order_id'),
        on='order_id',
        how='inner'
        ).resample(
            'ME', 
            on='order_purchase_timestamp'
            ).agg({
                'order_status': 'count',
                'payment_value': 'sum'
                })

def see_map(df, max_point):
    top_point = df.iloc[:max_point]
    geo_df = gpd.GeoDataFrame(top_point, geometry=gpd.points_from_xy(top_point['lat'], top_point['lng']))
    world = gpd.read_file(f'{CURRENT_DIR}/110m_cultural/ne_110m_admin_0_map_units.shp')
    fig, ax = plt.subplots()
    ax.set_xlim([top_point['lat'].min(), top_point['lat'].max()])
    ax.set_ylim([top_point['lng'].min(), top_point['lat'].max()])
    world.plot(ax=ax, color='white', edgecolor='black')
    geo_df.plot(ax=ax, column='jumlah', legend=True, legend_kwds={"label": "Sebaran pembeli", "orientation": "horizontal"})
    st.pyplot(fig)

def see_payment(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    bar_plot = sns.barplot(x='jumlah', y='payment_type', data=df, palette='viridis', ax=ax)
    for bar in bar_plot.patches:
        bar_value = bar.get_width()
        text = f'{bar_value:.0f}'
        text_x = bar.get_x() + bar_value + 10
        bar_plot.annotate(text, xy=(text_x, bar.get_y() + bar.get_height() / 2), va='center')
    ax.set_title('Metode pembayaran yang diminati')
    ax.set_xlabel('Jenis Pembayaran')
    ax.set_ylabel('Jumlah pembeli')
    st.pyplot(fig)

def see_trx(df):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(df['jumlah'], labels=df['order_status'],
            autopct='%1.4f%%', startangle=90, colors=plt.cm.viridis(range(len(df))),
            textprops={
                'color': 'white',
                'bbox': dict(facecolor='black', edgecolor='black', boxstyle='round,pad=0.5')
                })
    ax.set_title('Distribusi Keberhasilan pesanan')
    st.pyplot(fig)

def see_user(df):
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(df.index, df['order_status'], marker='o', linestyle='-', color='blue')
    ax1.set_title('Grafik jumlah pembeli per bulan')
    ax1.set_xlabel('Bulan')
    ax1.set_ylabel('Jumlah')
    ax1.grid(True)
    st.pyplot(fig1)
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.plot(df.index, df['payment_value'], marker='o', linestyle='-', color='blue')
    ax2.set_title('Grafik omzet per bulan')
    ax2.set_xlabel('Bulan')
    ax2.set_ylabel('Jumlah')
    ax2.grid(True)
    st.pyplot(fig2)

customers_df = pd.read_csv(CURRENT_DIR + '\customers_dataset.csv')
geolocation_df = pd.read_csv(CURRENT_DIR + '\geolocation_dataset.csv')
orders_df = pd.read_csv(CURRENT_DIR + '\orders_dataset.csv')
cleaning(orders_df)
payments_df = pd.read_csv(CURRENT_DIR + '\order_payments_dataset.csv')

groupby_city = grouping_geo(geolocation_df, customers_df)
groupby_payment = grouping_payment(payments_df)
groupby_status = grouping_status(orders_df)
groupby_trend = grouping_trend(orders_df, payments_df)


sns.set(style='dark')

st.title('Analisis pengguna E-Commerce')
st.text('By: Muhammad Ali Pratama')

tab1, tab2, tab3, tab4 = st.tabs(['Demografi', 'Metode Pembayaran', 'Status transaksi', 'Tren pengguna'])

with tab1:
    st.text('Lihat analisis  demografi pengguna')
    max_points = st.number_input(
        label='Maksimal data',
        value=4000,
        min_value=1,
        max_value=groupby_city.shape[0])
    see_map(groupby_city, int(max_points))

with tab2:
    st.text('Lihat Metode pembayaran yang banyak dipakai oleh pengguna')
    see_payment(groupby_payment)

with tab3:
    st.text('Lihat persentase status transaksi')
    see_trx(groupby_status)

with tab4:
    st.text('Lihat tren pengguna berdasarkan jumlah pengguna dan total pembayaran yang didapatkan oleh perusahaan')
    see_user(groupby_trend)

