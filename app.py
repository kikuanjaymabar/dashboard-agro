import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime

st.set_page_config(layout="wide", page_title="MES Dashboard")

css = """
<style>
.kpi-card { background: linear-gradient(135deg, #1E2530, #2A3441); padding: 20px; border-radius: 12px; border-left: 4px solid #00D4FF; margin-bottom: 10px; }
.kpi-label { color: #8B95A5; font-size: 13px; letter-spacing: 1px; }
.kpi-value { color: #FAFAFA; font-size: 32px; font-weight: bold; }
.kpi-delta-up { color: #00FF88; font-size: 13px; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

header_col1, header_col2, header_col3 = st.columns([1,2,3])
with header_col1:
    st.markdown("### MES")
with header_col3:
    st.markdown("SYSTEM ONLINE")
st.devider()

st.title("Dashboard Penjadwalan Produksi Agroindustri")
st.caption("Prototipe MES untuk optimasi penjadwalan produksi bahan baku mudah rusak")

st.sidebar.header("Input Parameter")
mesin = st.sidebar.slider("Jumlah Mesin", 1, 10, 3)
pesanan = st.sidebar.slider("Jumlah Pesanan", 5, 50, 10)
masa_simpan = st.sidebar.number_input("Masa Simpan Bahan (jam)", 1, 24, 6)
populasi = st.sidebar.slider("Ukuran Populasi GA", 10,200, 50)
geerasi = st.sidebar.slider("Jumlah Generasi GA", 10, 500, 100)

if pesanan > 20 and mesin < 3:
    st.warning("Bebam produksi tinggi. Pertimbangan tambah mesin.")
else:
    st.succes("Kapasitas produksi memadai.")

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Penjadwalan", "Analitik", "Pengaturan"])

with tab1:
    st.subheader("Ringkasan Kinerja")
    kpi1, kpi2, kpi3,kpi4 = st.columns(4)
    with kpi:
        st.markdown('<div class="kpi-card"><div class="kpi-label">MAKESPAN</div><div class="kpi-value">9 jam</div><div class="kpi-delta-up">Turun 2 jam vs Manual</div></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown('<div class="kpi-card"><div class="kpi-label">BAHAN RUSAK</div><div class="kpi-value">0 kg</div><div class="kpi-delta-up">Turun 5 kg vs Manual</div></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown('<div class="kpi-card"><div class="kpi-label">EFISIENSI</div><div class="kpi-value">94%</div><div class="kpi-delta-up">Naik 12% vs Manual</div></div>', unsafe_allow_html=True)
    with kpi4:
        st.markdown('<div class="kpi-card"><div class="kpi-label">STATUS</div><div class="kpi-value">Optimal</div><div class="kpi-delta-up">GA Konvergen</div></div>', unsafe_allow_html=True)

with tab2:
    st.subheader("Gantt Chart Penjadwalan Produksi")
    if st.button("Jalankan Algoritma Genetika"):
        with st.spinner("Menjalankan GA..."):
            time.sleep(2)
        st.success("GA berhasil dijalankan!")

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
        
        fig = px.timeline(data, x_start="Mulai", x_end="Selesai", y="Mesin", color="Pesanan")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
        
        csv = data.to_csv(index=False).encode("utf-8")
        st.download_button("Download Jadwal (CSV)", csv, "jadwal.csv", "text/csv")

with tab3:
    st.subheader("Konvergensi Algoritma Genetika")
    gens = list(range(1, generasi + 1))
    fitness_values = [100 - 80 * (1 - np.exp(-g / 20)) + np.random.normal(0, 0.5) for g in gens]
    fig_conv = go.Figure()
    fig_conv.add_trace(go.Scatter(x=gens, y=fitness_values, mode="lines", name="Fitness Terbaik", line=dict(color="#00D4FF", width=3)))
    fig_conv.update_layout(xaxis_title="Generasi", yaxis_title="Nilai Fitness", template="plotly_dark")
    st.plotly_chart(fig_conv, use_container_width=True)

with tab4:
    st.subheader("Parameter Algoritma Genetika")
    st.write("Populasi:", populasi)
    st.write("Generasi:", generasi)
    st.write("Metode Seleksi: Tournament")
    st.write("Metode Crossover: Order Crossover")
    st.write("Metode Mutasi: Swap Mutation")
    st.caption("Terakhir diperbarui: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
