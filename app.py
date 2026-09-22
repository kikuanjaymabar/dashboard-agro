import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime

st.set_page_config(layout="wide", page_title="MES Dashboard")

css = """
<style>
.kpi-card { background: linear-gradient(135deg, #1E2530, #2A3441); padding: 20px; border-radius: 12px; border-left: 4px solid #00D4FF; margin-bottom: 10px; }
.kpi-label { color: #8B95A5; font-size: 13px; letter-spacing: 1px; }
.kpi-value { color: #FAFAFA; font-size: 32px; font-weight: bold; }
.kpi-delta-up { color: #00FF88; font-size: 13px; }
.kpi-delta-down { color: #FF6B6B; font-size: 13px; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

def hitung_makespan(jadwal, waktu_proses):
    mesin_waktu = {}
    for mesin, pesanan in jadwal:
        if mesin not in mesin_waktu:
            mesin_waktu[mesin] = 0
        mesin_waktu[mesin] += waktu_proses[pesanan]
    return max(mesin_waktu.values())

def inisialisasi_populasi(pop_size, num_pesanan, num_mesin):
    populasi = []
    for _ in range(pop_size):
        urutan = list(range(num_pesanan))
        random.shuffle(urutan)
        individu = []
        for i, p in enumerate(urutan):
            individu.append((i % num_mesin, p))
        populasi.append(individu)
    return populasi

def fitness(individu, waktu_proses):
    return hitung_makespan(individu, waktu_proses)

def seleksi_tournament(populasi, waktu_proses, k=3):
    terpilih = random.sample(populasi, k)
    terpilih.sort(key=lambda x: fitness(x, waktu_proses))
    return terpilih[0]

def crossover(parent1, parent2):
    n = len(parent1)
    titik = random.randint(1, n - 1)
    anak = parent1[:titik] + parent2[titik:]
    return anak

def mutasi(individu, prob=0.1):
    individu = individu.copy()
    if random.random() < prob:
        i, j = random.sample(range(len(individu)), 2)
        individu[i], individu[j] = individu[j], individu[i]
    return individu

def jalankan_ga(pop_size, generasi, num_pesanan, num_mesin, waktu_proses):
    populasi = inisialisasi_populasi(pop_size, num_pesanan, num_mesin)
    riwayat_fitness = []
    for gen in range(generasi):
        populasi.sort(key=lambda x: fitness(x, waktu_proses))
        terbaik = populasi[0]
        riwayat_fitness.append(fitness(terbaik, waktu_proses))
        populasi_baru = [terbaik]
        while len(populasi_baru) < pop_size:
            p1 = seleksi_tournament(populasi, waktu_proses)
            p2 = seleksi_tournament(populasi, waktu_proses)
            anak = crossover(p1, p2)
            anak = mutasi(anak)
            populasi_baru.append(anak)
        populasi = populasi_baru
    populasi.sort(key=lambda x: fitness(x, waktu_proses))
    return populasi[0], riwayat_fitness

header_col1, header_col2, header_col3 = st.columns([1, 3, 1])
with header_col1:
    st.markdown("### MES")
with header_col3:
    st.markdown("SYSTEM ONLINE")
st.divider()

st.title("Dashboard Penjadwalan Produksi Agroindustri")
st.caption("Prototipe MES dengan Algoritma Genetika untuk optimasi penjadwalan bahan baku mudah rusak")

st.sidebar.header("Input Parameter")
mesin = st.sidebar.slider("Jumlah Mesin", 2, 10, 3)
pesanan = st.sidebar.slider("Jumlah Pesanan", 5, 30, 10)
masa_simpan = st.sidebar.number_input("Masa Simpan Bahan (jam)", 1, 24, 6)
populasi_ga = st.sidebar.slider("Ukuran Populasi GA", 10, 200, 50)
generasi_ga = st.sidebar.slider("Jumlah Generasi GA", 10, 300, 100)

st.sidebar.divider()
st.sidebar.subheader("Upload Data Produksi")
uploaded_file = st.sidebar.file_uploader("Upload CSV (opsional)", type=["csv"])
st.sidebar.caption("Format: kolom 'pesanan' dan 'waktu_proses'")

if pesanan > 20 and mesin < 3:
    st.warning("Beban produksi tinggi. Pertimbangkan tambah mesin.")
else:
    st.success("Kapasitas produksi memadai.")

if "hasil_ga" not in st.session_state:
    st.session_state.hasil_ga = None

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Penjadwalan", "Analitik", "Pengaturan"])

with tab1:
    st.subheader("Ringkasan Kinerja")
    if st.session_state.hasil_ga is not None:
        hasil = st.session_state.hasil_ga
        makespan_ga = hasil["makespan"]
        makespan_manual = hasil["makespan_manual"]
        selisih = makespan_manual - makespan_ga
        efisiensi = (selisih / makespan_manual) * 100
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">MAKESPAN GA</div><div class="kpi-value">{makespan_ga} jam</div><div class="kpi-delta-up">Turun {selisih} jam</div></div>', unsafe_allow_html=True)
        with kpi2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">MAKESPAN MANUAL</div><div class="kpi-value">{makespan_manual} jam</div><div class="kpi-delta-down">Baseline</div></div>', unsafe_allow_html=True)
        with kpi3:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">EFISIENSI</div><div class="kpi-value">{efisiensi:.1f}%</div><div class="kpi-delta-up">Naik vs Manual</div></div>', unsafe_allow_html=True)
        with kpi4:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">GENERASI</div><div class="kpi-value">{generasi_ga}</div><div class="kpi-delta-up">Konvergen</div></div>', unsafe_allow_html=True)
    else:
        st.info("Belum ada hasil. Buka tab 'Penjadwalan' dan klik 'Jalankan Algoritma Genetika'.")

with tab2:
    st.subheader("Gantt Chart Penjadwalan Produksi")
    if st.button("Jalankan Algoritma Genetika", type="primary"):
        with st.spinner("GA sedang berjalan..."):
            if uploaded_file is not None:
                df_user = pd.read_csv(uploaded_file)
                waktu_proses = dict(zip(range(len(df_user)), df_user["waktu_proses"].tolist()))
                num_pesanan = len(waktu_proses)
            else:
                waktu_proses = {i: random.randint(2, 8) for i in range(pesanan)}
                num_pesanan = pesanan
            hasil_terbaik, riwayat = jalankan_ga(populasi_ga, generasi_ga, num_pesanan, mesin, waktu_proses)
            makespan_ga = hitung_makespan(hasil_terbaik, waktu_proses)
            jadwal_manual = [(i % mesin, i) for i in range(num_pesanan)]
            makespan_manual = hitung_makespan(jadwal_manual, waktu_proses)
            st.session_state.hasil_ga = {
                "jadwal": hasil_terbaik,
                "riwayat": riwayat,
                "makespan": makespan_ga,
                "makespan_manual": makespan_manual,
                "waktu_proses": waktu_proses
            }
        st.success("GA berhasil dijalankan!")
        hasil = st.session_state.hasil_ga
        data_rows = []
        mesin_waktu = {}
        for m, p in hasil["jadwal"]:
            if m not in mesin_waktu:
                mesin_waktu[m] = 0
            mulai = mesin_waktu[m]
            selesai = mulai + hasil["waktu_proses"][p]
            mesin_waktu[m] = selesai
            data_rows.append({"Mesin": f"Mesin {m+1}", "Pesanan": f"P{p+1}", "Mulai": mulai, "Selesai": selesai})
        df_jadwal = pd.DataFrame(data_rows)
        base_date = pd.Timestamp("2024-01-01")
        df_jadwal["Mulai_dt"] = base_date + pd.to_timedelta(df_jadwal["Mulai"], unit="h")
        df_jadwal["Selesai_dt"] = base_date + pd.to_timedelta(df_jadwal["Selesai"], unit="h")
        fig = px.timeline(df_jadwal, x_start="Mulai_dt", x_end="Selesai_dt", y="Mesin", color="Pesanan")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_jadwal[["Mesin", "Pesanan", "Mulai", "Selesai"]], use_container_width=True)
        csv = df_jadwal[["Mesin", "Pesanan", "Mulai", "Selesai"]].to_csv(index=False).encode("utf-8")
        st.download_button("Download Jadwal (CSV)", csv, "jadwal_ga.csv", "text/csv")

with tab3:
    st.subheader("Konvergensi Algoritma Genetika")
    if st.session_state.hasil_ga is not None:
        riwayat = st.session_state.hasil_ga["riwayat"]
        gens = list(range(1, len(riwayat) + 1))
        fig_conv = go.Figure()
        fig_conv.add_trace(go.Scatter(x=gens, y=riwayat, mode="lines", name="Fitness Terbaik", line=dict(color="#00D4FF", width=3)))
        fig_conv.update_layout(xaxis_title="Generasi", yaxis_title="Makespan (jam)", template="plotly_dark")
        st.plotly_chart(fig_conv, use_container_width=True)
        st.metric("Makespan Awal", f"{riwayat[0]} jam")
        st.metric("Makespan Akhir", f"{riwayat[-1]} jam")
        st.metric("Perbaikan", f"{riwayat[0] - riwayat[-1]} jam")
    else:
        st.info("Jalankan GA dulu di tab 'Penjadwalan'.")

with tab4:
    st.subheader("Parameter Algoritma Genetika")
    st.write("Populasi:", populasi_ga)
    st.write("Generasi:", generasi_ga)
    st.write("Metode Seleksi: Tournament")
    st.write("Metode Crossover: Single Point")
    st.write("Metode Mutasi: Swap Mutation")
    st.divider()
    st.caption("Terakhir diperbarui: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if st.button("Refresh Timestamp"):
        st.rerun()
