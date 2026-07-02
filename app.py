import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# 1. SETUP DATABASE (Otomatis dibuat oleh Python, tidak perlu manual)
def init_db():
    conn = sqlite3.connect("database_nelayan.db")
    cursor = conn.cursor()
    # Tabel Bon Belanja
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bon_nelayan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            nama TEXT,
            keperluan TEXT,
            nominal INTEGER,
            status TEXT DEFAULT 'Belum Lunas',
            tanggal_lunas TEXT DEFAULT '-'
        )
    ''')
    # Tabel Pendapatan/Totalan Hasil Laut
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS totalan_laut (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            nama TEXT,
            pendapatan INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 2. KONFIGURASI HALAMAN STREAMLIT
st.set_page_config(page_title="Sistem Nelayan", layout="centered")
st.markdown("<h2 style='text-align: center;'>⚓ MasdabiyaNet Nelayan</h2>", unsafe_allow_html=True)

# Fungsi ambil data dari SQLite
def ambil_koneksi():
    return sqlite3.connect("database_nelayan.db")

conn = ambil_koneksi()

# 3. HITUNG RINGKASAN DATA (DASHBOARD)
total_bon = pd.read_sql_query("SELECT SUM(nominal) FROM bon_nelayan WHERE status='Belum Lunas'", conn).iloc[0,0] or 0
total_masuk = pd.read_sql_query("SELECT SUM(pendapatan) FROM totalan_laut", conn).iloc[0,0] or 0

# Tampilan Kartu Ringkasan
col1, col2 = st.columns(2)
with col1:
    st.error(f"🔴 **TOTAL BON**\n\nRp {total_bon:,.0f}")
with col2:
    st.success(f"🟢 **TOTALAN LAUT**\n\nRp {total_masuk:,.0f}")

st.markdown("---")

# 4. MENU NAVIGASI (Sangat ramah layar HP)
menu = st.radio("Pilih Menu:", ["🛒 Catat Bon Baru", "🐟 Catat Totalan Ikan", "📋 Daftar Bon Belum Lunas"], horizontal=True)

# --- MENU: CATAT BON BARU ---
if menu == "🛒 Catat Bon Baru":
    st.subheader("Form Bon Belanja Toko")
    with st.form("form_bon", clear_on_submit=True):
        nama = st.text_input("Nama Nelayan / Kapal")
        keperluan = st.text_input("Keperluan (Solar / Es / Sembako)")
        nominal = st.number_input("Nominal Bon (Rp)", min_value=0, step=50000)
        submit = st.form_submit_button("Simpan Data Bon")
        
        if submit and nama and keperluan and nominal > 0:
            tgl = datetime.now().strftime('%Y-%m-%d')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO bon_nelayan (tanggal, nama, keperluan, nominal) VALUES (?, ?, ?, ?)", (tgl, nama, keperluan, nominal))
            conn.commit()
            st.success("Data Bon berhasil disimpan!")
            st.rerun()

# --- MENU: CATAT TOTALAN IKAN ---
elif menu == "🐟 Catat Totalan Ikan":
    st.subheader("Form Hasil Jual Ikan")
    with st.form("form_tangkapan", clear_on_submit=True):
        nama = st.text_input("Nama Nelayan / Kapal")
        pendapatan = st.number_input("Total Hasil Penjualan (Rp)", min_value=0, step=100000)
        submit = st.form_submit_button("Simpan Hasil Layar")
        
        if submit and nama and pendapatan > 0:
            tgl = datetime.now().strftime('%Y-%m-%d')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO totalan_laut (tanggal, nama, pendapatan) VALUES (?, ?, ?)", (tgl, nama, pendapatan))
            conn.commit()
            st.success("Data Totalan Hasil Laut berhasil disimpan!")
            st.rerun()

# --- MENU: DAFTAR BON & POTONG TOTALAN ---
elif menu == "📋 Daftar Bon Belum Lunas":
    st.subheader("Daftar Hutang Bon")
    df_bon = pd.read_sql_query("SELECT id, tanggal, nama, keperluan, nominal FROM bon_nelayan WHERE status='Belum Lunas'", conn)
    
    if df_bon.empty:
        st.info("Semua bon nelayan sudah Lunas! 🎉")
    else:
        for idx, row in df_bon.iterrows():
            with st.container(border=True):
                col_text, col_btn = st.columns([2, 1])
                with col_text:
                    st.markdown(f"**{row['nama']}**")
                    st.caption(f"{row['keperluan']} ({row['tanggal']})")
                    st.markdown(f"<span style='color:red; font-weight:bold;'>Rp {row['nominal']:,.0f}</span>", unsafe_allow_html=True)
                with col_btn:
                    # Tombol aksi potong totalan langsung di setiap baris data
                    if st.button("Set Lunas", key=f"btn_{row['id']}"):
                        tgl_sekarang = datetime.now().strftime('%Y-%m-%d')
                        cursor = conn.cursor()
                        cursor.execute("UPDATE bon_nelayan SET status='Lunas', tanggal_lunas=? WHERE id=?", (tgl_sekarang, row['id']))
                        conn.commit()
                        st.success(f"Bon {row['nama']} Berhasil Dilunasi!")
                        st.rerun()
conn.close()
