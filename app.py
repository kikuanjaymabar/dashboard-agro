import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime
import io
from sklearn.ensemble import RandomForestRegressor

st.set_page_config(layout="wide", page_title="MES Dashboard v2")

css = """
<style>
.kpi-card { background: linear-gradient(135deg, #1E2530, #2A3441); padding: 20px; border-radius: 12px; border-left: 4px solid #00D4FF; margin-bottom: 10px; }
.kpi-label { color: #8B95A5; font-size: 13px; letter-spacing: 1px; }
.kpi-value { color: #FAFAFA; font-size: 32px; font-weight: bold; }
.kpi-delta-up { color: #00FF88; font-size: 13px; }
.kpi-delta-down { color: #FF6B6B; font-size: 13px; }
.oee-card { background: #1E2530; padding: 20px; border-radius: 10px; text-align: center; border-top: 4px solid #00D4FF; }
.oee-value { font-size: 36px; font-weight: bold; color: #FAFAFA; }
.oee-label { font-size: 12px; color: #8B95A5; letter-spacing: 1px; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

def hitung_makespan(jadwal, waktu_proses):
    mw = {}
    for m, p in jadwal:
        mw[m] = mw.get(m, 0) + waktu_proses[p]
    return max(mw.values()) if mw else 0

def hitung_utilisasi(jadwal, waktu_proses, num_mesin, makespan):
    mw = {i: 0 for i in range(num_mesin)}
    for m, p in jadwal:
        mw[m] += waktu_proses[p]
    return {i: (mw[i] / makespan * 100 if makespan > 0 else 0) for i in mw}

def hitung_oee(jadwal, waktu_proses, num_mesin, makespan, masa_simpan):
    if makespan == 0:
        return 0, 0, 0, 0
    total_proses = sum(waktu_proses.values())
    total_waktu = makespan * num_mesin
    availability = (total_proses / total_waktu) * 100
    util = hitung_utilisasi(jadwal, waktu_proses, num_mesin, makespan)
    performance = min(sum(util.values()) / len(util), 100)
    mw = {i: 0 for i in range(num_mesin)}
    selesai_per_p = {}
    for m, p in jadwal:
        mulai = mw[m]
        selesai = mulai + waktu_proses[p]
        mw[m] = selesai
        selesai_per_p[p] = selesai
    rusak = sum(1 for p, s in selesai_per_p.items() if s > masa_simpan)
    quality = ((len(waktu_proses) - rusak) / len(waktu_proses)) * 100
    oee = (availability / 100) * (performance / 100) * (quality / 100) * 100
    return availability, performance, quality, oee

def ga_init(pop, n, m):
    return [[(i % m, p) for i, p in enumerate(random.sample(range(n), n))] for _ in range(pop)]

def ga_fit(ind, wp):
    return hitung_makespan(ind, wp)

def ga_tour(pop, wp, k=3):
    s = random.sample(pop, k)
    s.sort(key=lambda x: ga_fit(x, wp))
    return s[0]

def ga_cross(p1, p2):
    t = random.randint(1, len(p1) - 1)
    return p1[:t] + p2[t:]

def ga_mut(ind, prob=0.1):
    ind = ind.copy()
    if random.random() < prob:
        i, j = random.sample(range(len(ind)), 2)
        ind[i], ind[j] = ind[j], ind[i]
    return ind

def jalankan_ga(pop_size, gen, n, m, wp):
    pop = ga_init(pop_size, n, m)
    riwayat = []
    for g in range(gen):
        pop.sort(key=lambda x: ga_fit(x, wp))
        riwayat.append(ga_fit(pop[0], wp))
        baru = [pop[0]]
        while len(baru) < pop_size:
            p1 = ga_tour(pop, wp)
            p2 = ga_tour(pop, wp)
            baru.append(ga_mut(ga_cross(p1, p2)))
        pop = baru
    pop.sort(key=lambda x: ga_fit(x, wp))
    return pop[0], riwayat

def pso_fit(pos, wp, n, m):
    urut = sorted(range(n), key=lambda i: pos[i])
    jadwal = [(i % m, p) for i, p in enumerate(urut)]
    return hitung_makespan(jadwal, wp), jadwal

def jalankan_pso(pop_size, iterasi, n, m, wp):
    pos = [[random.random() for _ in range(n)] for _ in range(pop_size)]
    vel = [[0.0] * n for _ in range(pop_size)]
    pbest = [p.copy() for p in pos]
    pbest_fit = [pso_fit(p, wp, n, m)[0] for p in pos]
    gbest = pbest[pbest_fit.index(min(pbest_fit))].copy()
    gbest_fit = min(pbest_fit)
    riwayat = []
    for it in range(iterasi):
        for i in range(pop_size):
            for d in range(n):
                r1, r2 = random.random(), random.random()
                vel[i][d] = 0.5 * vel[i][d] + 1.5 * r1 * (pbest[i][d] - pos[i][d]) + 1.5 * r2 * (gbest[d] - pos[i][d])
                pos[i][d] += vel[i][d]
            f = pso_fit(pos[i], wp, n, m)[0]
            if f < pbest_fit[i]:
                pbest_fit[i] = f
                pbest[i] = pos[i].copy()
                if f < gbest_fit:
                    gbest_fit = f
                    gbest = pos[i].copy()
        riwayat.append(gbest_fit)
    _, jadwal = pso_fit(gbest, wp, n, m)
    return jadwal, riwayat

def sa_fit(jadwal, wp):
    return hitung_makespan(jadwal, wp)

def jalankan_sa(iterasi, n, m, wp, suhu=100.0, cool=0.95):
    urut = list(range(n))
    random.shuffle(urut)
    jadwal = [(i % m, p) for i, p in enumerate(urut)]
    fit_now = sa_fit(jadwal, wp)
    terbaik = jadwal.copy()
    terbaik_fit = fit_now
    riwayat = []
    for it in range(iterasi):
        i, j = random.sample(range(len(jadwal)), 2)
        kand = jadwal.copy()
        kand[i], kand[j] = kand[j], kand[i]
        f_kand = sa_fit(kand, wp)
        d = f_kand - fit_now
        if d < 0 or random.random() < np.exp(-d / suhu):
            jadwal = kand
            fit_now = f_kand
            if fit_now < terbaik_fit:
                terbaik = jadwal.copy()
                terbaik_fit = fit_now
        suhu *= cool
        riwayat.append(terbaik_fit)
    return terbaik, riwayat

def latih_model_prediksi():
    np.random.seed(42)
    n = 200
    X = np.random.randint(1, 10, size=(n, 3))
    y = X[:, 0] * 1.5 + X[:, 1] * 0.8 + X[:, 2] * 0.5 + np.random.normal(0, 0.5, n)
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)
    return model

header1, header2, header3 = st.columns([1, 3, 1])
with header1:
    st.markdown("### MES")
with header3:
    st.markdown("SYSTEM ONLINE")
st.divider()

st.title("Dashboard Penjadwalan Produksi Agroindustri")
st.caption("MES Prototype v2 dengan Multi-Algoritma, OEE, dan Predictive Analytics")

st.sidebar.header("Input Parameter")
mesin = st.sidebar.slider("Jumlah Mesin", 2, 10, 3)
pesanan = st.sidebar.slider("Jumlah Pesanan", 5, 30, 12)
masa_simpan = st.sidebar.number_input("Masa Simpan Bahan (jam)", 1, 24, 6)
pop_ga = st.sidebar.slider("Populasi GA", 10, 100, 30)
gen_ga = st.sidebar.slider("Generasi GA", 10, 200, 50)
iter_pso = st.sidebar.slider("Iterasi PSO", 10, 200, 50)
iter_sa = st.sidebar.slider("Iterasi SA", 10, 500, 100)

if pesanan > 20 and mesin < 3:
    st.warning("Beban produksi tinggi. Pertimbangkan tambah mesin.")
else:
    st.success("Kapasitas produksi memadai.")

if "hasil" not in st.session_state:
    st.session_state.hasil = None
if "history" not in st.session_state:
    st.session_state.history = []

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Penjadwalan", "Perbandingan Algoritma", "OEE & Utilisasi", "Predictive"])

with tab1:
    st.subheader("Ringkasan Kinerja")
    if st.session_state.hasil is not None:
        h = st.session_state.hasil
        selisih = h["makespan_manual"] - h["makespan_ga"]
        efisiensi = (selisih / h["makespan_manual"]) * 100 if h["makespan_manual"] > 0 else 0
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">MAKESPAN GA</div><div class="kpi-value">{h["makespan_ga"]} jam</div><div class="kpi-delta-up">Turun {selisih} jam</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">MAKESPAN MANUAL</div><div class="kpi-value">{h["makespan_manual"]} jam</div><div class="kpi-delta-down">Baseline</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">EFISIENSI</div><div class="kpi-value">{efisiensi:.1f}%</div><div class="kpi-delta-up">Naik vs Manual</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">OEE</div><div class="kpi-value">{h["oee"]:.1f}%</div><div class="kpi-delta-up">World Class: 85%</div></div>', unsafe_allow_html=True)
    else:
        st.info("Jalankan algoritma di tab Penjadwalan dulu.")

with tab2:
    st.subheader("Gantt Chart Penjadwalan")
    if st.button("Jalankan GA", type="primary"):
        with st.spinner("GA berjalan..."):
            wp = {i: random.randint(2, 8) for i in range(pesanan)}
            jadwal, riwayat = jalankan_ga(pop_ga, gen_ga, pesanan, mesin, wp)
            mk_ga = hitung_makespan(jadwal, wp)
            jadwal_manual = [(i % mesin, i) for i in range(pesanan)]
            mk_manual = hitung_makespan(jadwal_manual, wp)
            av, pf, ql, oe = hitung_oee(jadwal, wp, mesin, mk_ga, masa_simpan)
            st.session_state.hasil = {
                "jadwal": jadwal, "riwayat": riwayat, "wp": wp,
                "makespan_ga": mk_ga, "makespan_manual": mk_manual,
                "av": av, "pf": pf, "ql": ql, "oee": oe
            }
            st.session_state.history.append({
                "Waktu": datetime.now().strftime("%H:%M:%S"),
                "Mesin": mesin, "Pesanan": pesanan,
                "Makespan": mk_ga, "OEE": round(oe, 1)
            })
        st.success("GA selesai!")
    if st.session_state.hasil is not None:
        h = st.session_state.hasil
        mw = {}
        rows = []
        for m, p in h["jadwal"]:
            mulai = mw.get(m, 0)
            selesai = mulai + h["wp"][p]
            mw[m] = selesai
            rows.append({"Mesin": f"Mesin {m+1}", "Pesanan": f"P{p+1}", "Mulai": mulai, "Selesai": selesai, "Status": "OK" if selesai <= masa_simpan else "RUSAK"})
        df = pd.DataFrame(rows)
        base = pd.Timestamp("2024-01-01")
        df["Mulai_dt"] = base + pd.to_timedelta(df["Mulai"], unit="h")
        df["Selesai_dt"] = base + pd.to_timedelta(df["Selesai"], unit="h")
        fig = px.timeline(df, x_start="Mulai_dt", x_end="Selesai_dt", y="Mesin", color="Pesanan")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["Mesin", "Pesanan", "Mulai", "Selesai", "Status"]], use_container_width=True)

with tab3:
    st.subheader("Perbandingan GA vs PSO vs SA")
    if st.button("Jalankan Semua Algoritma"):
        with st.spinner("Menjalankan ketiga algoritma..."):
            wp = {i: random.randint(2, 8) for i in range(pesanan)}
            _, r_ga = jalankan_ga(pop_ga, gen_ga, pesanan, mesin, wp)
            _, r_pso = jalankan_pso(pop_ga, iter_pso, pesanan, mesin, wp)
            _, r_sa = jalankan_sa(iter_sa, pesanan, mesin, wp)
            st.session_state.perbandingan = {"ga": r_ga, "pso": r_pso, "sa": r_sa}
    if "perbandingan" in st.session_state:
        p = st.session_state.perbandingan
        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Scatter(y=p["ga"], name="GA", line=dict(color="#00D4FF", width=3)))
        fig_cmp.add_trace(go.Scatter(y=p["pso"], name="PSO", line=dict(color="#FF6B6B", width=3)))
        fig_cmp.add_trace(go.Scatter(y=p["sa"], name="SA", line=dict(color="#00FF88", width=3)))
        fig_cmp.update_layout(xaxis_title="Iterasi/Generasi", yaxis_title="Makespan Terbaik", template="plotly_dark")
        st.plotly_chart(fig_cmp, use_container_width=True)
        hasil_akhir = pd.DataFrame({
            "Algoritma": ["GA", "PSO", "SA"],
            "Makespan Akhir": [p["ga"][-1], p["pso"][-1], p["sa"][-1]]
        })
        st.dataframe(hasil_akhir, use_container_width=True)

with tab4:
    st.subheader("OEE & Utilisasi Mesin")
    if st.session_state.hasil is not None:
        h = st.session_state.hasil
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="oee-card"><div class="oee-value">{h["av"]:.1f}%</div><div class="oee-label">AVAILABILITY</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="oee-card"><div class="oee-value">{h["pf"]:.1f}%</div><div class="oee-label">PERFORMANCE</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="oee-card"><div class="oee-value">{h["ql"]:.1f}%</div><div class="oee-label">QUALITY</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="oee-card"><div class="oee-value">{h["oee"]:.1f}%</div><div class="oee-label">OEE</div></div>', unsafe_allow_html=True)
        st.divider()
        util = hitung_utilisasi(h["jadwal"], h["wp"], mesin, h["makespan_ga"])
        df_util = pd.DataFrame({"Mesin": [f"Mesin {k+1}" for k in util.keys()], "Utilisasi (%)": list(util.values())})
        fig_util = px.bar(df_util, x="Mesin", y="Utilisasi (%)", color="Utilisasi (%)", color_continuous_scale="Blues")
        st.plotly_chart(fig_util, use_container_width=True)
    else:
        st.info("Jalankan GA dulu di tab Penjadwalan.")

with tab5:
    st.subheader("Prediksi Waktu Proses (Machine Learning)")
    st.caption("Random Forest memprediksi waktu proses berdasarkan 3 parameter input")
    model = latih_model_prediksi()
    c1, c2, c3 = st.columns(3)
    with c1:
        f1 = st.number_input("Kompleksitas Produk (1-10)", 1, 10, 5)
    with c2:
        f2 = st.number_input("Jumlah Bahan (1-10)", 1, 10, 5)
    with c3:
        f3 = st.number_input("Tingkat Kesulitan (1-10)", 1, 10, 5)
    if st.button("Prediksi Waktu Proses"):
        pred = model.predict([[f1, f2, f3]])[0]
        st.metric("Prediksi Waktu Proses", f"{pred:.2f} jam")
    st.divider()
    st.subheader("Riwayat Penjadwalan")
    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
    else:
        st.info("Belum ada riwayat.")

st.sidebar.divider()
st.sidebar.caption("Terakhir: " + datetime.now().strftime("%H:%M:%S"))
