import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# 1. SETUP DATABASE (Khusus rincian KM QOLBIYA)
def init_db():
    conn = sqlite3.connect("database_qolbiya.db")
    cursor = conn.cursor()
    # Tabel Pengeluaran / Bon Perbekalan
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perbekalan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            jenis_item TEXT,
            nominal INTEGER,
            status TEXT DEFAULT 'Belum Lunas'
        )
    ''')
    # Tabel Pendapatan Kotor (Hasil Jual Ikan)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS penjualan_ikan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            pendapatan_kotor INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Konfigurasi Halaman Ringkas HP
st.set_page_config(page_title="KM QOLBIYA", layout="centered")
st.markdown("<h2 style='text-align: center;'>⚓ KM QOLBIYA</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Sistem Manajemen Totalan Hasil Layar</p>", unsafe_allow_html=True)

def get_connection():
    return sqlite3.connect("database_qolbiya.db")

conn = get_connection()

# 2. HITUNG LOGIKA MATEMATIKA OTOMATIS
# Ambil total bon perbekalan yang belum dibayar/belum ditotal
total_perbekalan = pd.read_sql_query("SELECT SUM(nominal) FROM perbekalan WHERE status='Belum Lunas'", conn).iloc[0,0] or 0
# Ambil total pendapatan kotor terakhir (atau akumulasi)
total_pendapatan_kotor = pd.read_sql_query("SELECT SUM(pendapatan_kotor) FROM penjualan_ikan", conn).iloc[0,0] or 0
# Hitung sisa bersih otomatis
sisa_bersih = total_pendapatan_kotor - total_perbekalan

# 3. DASHBOARD TOTALAN (Tampilan Angka Besar di HP)
st.markdown("### 📊 Ringkasan Keuangan")
st.error(f"📦 **Total Bon Perbekalan (Es + Solar dll):**\n\nRp {total_perbekalan:,.0f}")
st.success(f"💰 **Pendapatan Kotor Jual Ikan:**\n\nRp {total_pendapatan_kotor:,.0f}")

if sisa_bersih >= 0:
    st.info(f"💵 **SISA BERSIH (Bagi Hasil):**\n\nRp {sisa_bersih:,.0f}")
else:
    st.warning(f"⚠️ **Minus (Pendapatan kurang dari modal):**\n\nRp {sisa_bersih:,.0f}")

st.markdown("---")

# 4. MENU NAVIGASI INPUT
menu = st.radio("Pilih Kegiatan:", ["🛒 Input Bon Perbekalan", "🐟 Input Hasil Jual Ikan", "📋 Rincian Bon Aktif"], horizontal=True)

# --- MENU 1: INPUT BON PERBEKALAN ---
if menu == "🛒 Input Bon Perbekalan":
    st.subheader("📝 Catat Pengeluaran Bon")
    with st.form("form_perbekalan", clear_on_submit=True):
        jenis_item = st.selectbox("Jenis Perbekalan:", ["Solar", "Es Batu", "Logistik/Sembako", "Uang Saku ABK", "Lainnya"])
        keterangan_tambahan = st.text_input("Keterangan Tambahan (Misal: Toko A / Jumlah)")
        nominal = st.number_input("Nominal Pengeluaran (Rp)", min_value=0, step=50000)
        submit = st.form_submit_button("Simpan Pengeluaran")
        
        if submit and nominal > 0:
            tgl = datetime.now().strftime('%Y-%m-%d')
            item_final = f"{jenis_item} ({keterangan_tambahan})" if keterangan_tambahan else jenis_item
            cursor = conn.cursor()
            cursor.execute("INSERT INTO perbekalan (tanggal, jenis_item, nominal) VALUES (?, ?, ?)", (tgl, item_final, nominal))
            conn.commit()
            st.success(f"Berhasil mencatat bon {item_final} senilai Rp {nominal:,.0f}")
            st.rerun()

# --- MENU 2: INPUT HASIL JUAL IKAN ---
elif menu == "🐟 Input Hasil Jual Ikan":
    st.subheader("💰 Catat Pendapatan Penjualan")
    with st.form("form_jual", clear_on_submit=True):
        st.write("Masukkan total uang yang didapat dari penjualan ikan setelah berlayar.")
        pendapatan = st.number_input("Total Uang Hasil Ikan (Rp)", min_value=0, step=500000)
        submit = st.form_submit_button("Simpan Hasil Jual")
        
        if submit and pendapatan > 0:
            tgl = datetime.now().strftime('%Y-%m-%d')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO penjualan_ikan (tanggal, pendapatan_kotor) VALUES (?, ?)", (tgl, pendapatan))
            conn.commit()
            st.success(f"Hasil penjualan Rp {pendapatan:,.0f} berhasil masuk sistem!")
            st.rerun()

# --- MENU 3: RINCIAN BON AKTIF & KLIK TOTALAN ---
elif menu == "📋 Rincian Bon Aktif":
    st.subheader("📑 Item Bon Belum Dibayar")
    df_bon = pd.read_sql_query("SELECT id, tanggal, jenis_item, nominal FROM perbekalan WHERE status='Belum Lunas'", conn)
    
    if df_bon.empty:
        st.info("Tidak ada bon aktif. Perbekalan bersih!")
    else:
        # Tampilkan rincian per item
        for idx, row in df_bon.iterrows():
            with st.container(border=True):
                st.markdown(f"🔹 **{row['jenis_item']}**")
                st.caption(f"Tanggal input: {row['tanggal']}")
                st.markdown(f"<span style='color:red; font-weight:bold;'>Rp {row['nominal']:,.0f}</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        # Tombol Sakti buat reset/bersihkan bon pas sudah totalan besar
        st.write("⚠️ **Tombol Totalan Akhir Layar**\nKlik tombol di bawah jika kapal sudah pulang, ikan terjual, dan semua bon di atas ingin dianggap **Lunas/Dipotong** untuk pelayaran ini.")
        
        if st.button("🔴 LUNASKAN SEMUA BON & RESET PENJUALAN"):
            cursor = conn.cursor()
            # Set semua bon lama jadi lunas
            cursor.execute("UPDATE perbekalan SET status='Lunas'")
            # Kosongkan record pendapatan kotor untuk persiapan pelayaran berikutnya
            cursor.execute("DELETE FROM penjualan_ikan")
            conn.commit()
            st.success("Semua bon telah dipotong! Sistem siap mencatat perbekalan pelayaran berikutnya.")
            st.rerun()

conn.close()
