import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(layout="wide", page_title="MES Dashboard")

st.title("Dashboard Penjadwalan Produksi Agroindustri")
st.markdown("Prototipe MES untuk optimasi penjadwalan produksi bahan baku mudah rusak.")

st.sidebar.header("Input Parameter")
mesin = st.sidebar.slider("Jumlah Mesin", 1, 10, 3)
pesanan = st.sidebar.slider("Jumlah Pesanan", 5, 50, 10)
masa_simpan = st.sidebar.number_input("Masa Simpan Bahan (jam)", 1, 24, 6)

if st.sidebar.button("Jalankan Algoritma Genetika"):
    with st.spinner("Menjalankan GA..."):
        time.sleep(2)
    
    st.success("GA berhasil dijalankan!")
    
    data = pd.DataFrame({
        "Mesin": ["Mesin 1", "Mesin 1", "Mesin 2", "Mesin 2", "Mesin 3"],
        "Pesanan": ["P3", "P7", "P5", "P2", "P4"],
        "Mulai": [0, 4, 0, 5, 0],
        "Selesai": [4, 8, 5, 9, 6]
    })

    base_date = pd.Timestamp("2024-01-01")
    data["Mulai"] = base_date + pd.to_timedelta(data["Mulai"], unit="h")
    data["Selesai"] = base_date + pd.to_timedelta(data["Selesai"], unit="h")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Makespan", "9 jam", "-2 jam vs Manual")
    with col2:
        st.metric("Bahan Rusak", "0 kg", "-5 kg vs Manual")
    
    fig = px.timeline(data, x_start="Mulai", x_end="Selesai", y="Mesin", color="Pesanan")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Klik 'Jalankan Algoritma Genetika' di sidebar untuk memulai.")
