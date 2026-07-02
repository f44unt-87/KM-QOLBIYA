import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import urllib.parse

# 1. SETUP DATABASE
def init_db():
    conn = sqlite3.connect("database_qolbiya.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perbekalan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            jenis_item TEXT,
            nominal INTEGER,
            status TEXT DEFAULT 'Belum Lunas'
        )
    ''')
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

# KONFIGURASI TAMPILAN HP
st.set_page_config(page_title="KM QOLBIYA", layout="centered")
st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>⚓ KM QOLBIYA</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'>Sistem Manajemen Hasil Layar</p>", unsafe_allow_html=True)

def get_connection():
    return sqlite3.connect("database_qolbiya.db")

conn = get_connection()

# AMBIL DATA UNTUK KALKULASI TOTALAN
total_perbekalan = pd.read_sql_query("SELECT SUM(nominal) FROM perbekalan WHERE status='Belum Lunas'", conn).iloc[0,0] or 0
total_pendapatan_kotor = pd.read_sql_query("SELECT SUM(pendapatan_kotor) FROM penjualan_ikan", conn).iloc[0,0] or 0
sisa_bersih = total_pendapatan_kotor - total_perbekalan

# --- MEMBUAT 3 TAB ---
tab1, tab2, tab3 = st.tabs(["🛒 Input Bon", "🐟 Input Jual Ikan", "📋 Laporan Totalan"])

# ==================== TAB 1: INPUT BON ====================
with tab1:
    st.markdown("### 🛒 Catat Pengeluaran Bon")
    with st.form("form_perbekalan", clear_on_submit=True):
        jenis_item = st.selectbox("Jenis Perbekalan:", ["Solar", "Es Batu", "Logistik/Sembako", "Uang Saku ABK", "Lainnya"])
        keterangan_tambahan = st.text_input("Keterangan Tambahan (Toko / Jumlah)")
        nominal = st.number_input("Nominal Pengeluaran (Rp)", min_value=0, step=50000)
        submit = st.form_submit_button("Simpan Pengeluaran")
        
        if submit and nominal > 0:
            tgl = datetime.now().strftime('%Y-%m-%d')
            item_final = f"{jenis_item} ({keterangan_tambahan})" if keterangan_tambahan else jenis_item
            cursor = conn.cursor()
            cursor.execute("INSERT INTO perbekalan (tanggal, jenis_item, nominal) VALUES (?, ?, ?)", (tgl, item_final, nominal))
            conn.commit()
            st.success(f"Tercatat: {item_final} - Rp {nominal:,.0f}")
            st.rerun()

# ==================== TAB 2: INPUT JUAL IKAN ====================
with tab2:
    st.markdown("### 🐟 Catat Pendapatan Penjualan")
    with st.form("form_jual", clear_on_submit=True):
        pendapatan = st.number_input("Total Uang Hasil Jual Ikan (Rp)", min_value=0, step=500000)
        submit = st.form_submit_button("Simpan Hasil Jual")
        
        if submit and pendapatan > 0:
            tgl = datetime.now().strftime('%Y-%m-%d')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM penjualan_ikan")
            cursor.execute("INSERT INTO penjualan_ikan (tanggal, pendapatan_kotor) VALUES (?, ?)", (tgl, pendapatan))
            conn.commit()
            st.success(f"Hasil penjualan Rp {pendapatan:,.0f} berhasil disimpan!")
            st.rerun()

# ==================== TAB 3: LAPORAN, EDIT, & NOTA ====================
with tab3:
    st.markdown("### 📊 Ringkasan Keuangan Saat Ini")
    
    # Kartu Informasi Utama
    st.error(f"📦 **Total Bon:** Rp {total_perbekalan:,.0f}")
    st.success(f"💰 **Pendapatan Kotor:** Rp {total_pendapatan_kotor:,.0f}")
    st.info(f"💵 **SISA BERSIH:** Rp {sisa_bersih:,.0f}")
    
    st.markdown("---")
    st.markdown("#### 📑 Rincian Tabel Pengeluaran (Bon Aktif)")
    
    df_bon = pd.read_sql_query("SELECT id, tanggal AS Tanggal, jenis_item AS [Keterangan Bon], nominal AS [Nominal (Rp)] FROM perbekalan WHERE status='Belum Lunas'", conn)
    
    if df_bon.empty:
        st.info("Belum ada rincian bon belanja.")
        edited_df = df_bon
    else:
        edited_df = st.data_editor(
            df_bon, 
            use_container_width=True, 
            hide_index=True,
            column_config={"id": None},
            num_rows="dynamic"
        )
        
        if not edited_df.equals(df_bon):
            if st.button("💾 Simpan Perubahan Tabel", type="secondary", use_container_width=True):
                cursor = conn.cursor()
                current_ids = edited_df['id'].tolist() if 'id' in edited_df.columns else []
                for original_id in df_bon['id'].tolist():
                    if original_id not in current_ids:
                        cursor.execute("DELETE FROM perbekalan WHERE id = ?", (original_id,))
                
                for _, row in edited_df.iterrows():
                    cursor.execute(
                        "UPDATE perbekalan SET jenis_item = ?, [nominal] = ? WHERE id = ?",
                        (row['Keterangan Bon'], row['Nominal (Rp)'], row['id'])
                    )
                conn.commit()
                st.success("Perubahan berhasil disimpan!")
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### 📱 Aksi Nota & Totalan")
        
        # 1. LOGIKA TEKS KHUSUS WHATSAPP
        text_wa = f"*NOTA TOTALAN KM QOLBIYA*\n"
        text_wa += f"Tanggal: {datetime.now().strftime('%d-%m-%Y %H:%M')}\n\n"
        text_wa += f"*Rincian Pengeluaran Bon:*\n"
        for _, r in edited_df.iterrows():
            text_wa += f"- {r['Keterangan Bon']}: Rp {r['Nominal (Rp)']:,.0f}\n"
        text_wa += f"\n----------------------------------------\n"
        text_wa += f"📦 *Total Bon:* Rp {total_perbekalan:,.0f}\n"
        text_wa += f"💰 *Pendapatan Kotor:* Rp {total_pendapatan_kotor:,.0f}\n"
        text_wa += f"💵 *SISA BERSIH:* Rp {sisa_bersih:,.0f}\n"
        text_wa += f"----------------------------------------\n"
        text_wa += f"_Sistem Catatan MasdabiyaNet_"
        
        encoded_text = urllib.parse.quote(text_wa)
        link_wa = f"https://wa.me/6281353539600?text={encoded_text}"
        
        # 2. LOGIKA STRUK STRUKTURAL UNTUK DI-PRINT (TERSEMBUNYI)
        html_print_content = f"""
        <div style='font-family:Courier,monospace; width:280px; padding:10px; font-size:12px; line-height:1.4;'>
            <center><b>NOTA TOTALAN KM QOLBIYA</b><br>Tgl: {datetime.now().strftime('%d-%m-%Y %H:%M')}</center>
            ------------------------------------<br>
            <b>RINCIAN PENGELUARAN BON:</b><br>
        """
        for _, r in edited_df.iterrows():
            html_print_content += f"- {r['Keterangan Bon']}:<br>&nbsp;&nbsp;Rp {r['Nominal (Rp)']:,.0f}<br>"
        html_print_content += f"""
            ------------------------------------<br>
            📦 Total Bon&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: Rp {total_perbekalan:,.0f}<br>
            💰 Pend. Kotor&nbsp;&nbsp;&nbsp;: Rp {total_pendapatan_kotor:,.0f}<br>
            ====================================<br>
            💵 <b>SISA BERSIH&nbsp;&nbsp;: Rp {sisa_bersih:,.0f}</b><br>
            ------------------------------------<br>
            <center><i>Sistem Catatan MasdabiyaNet</i></center>
        </div>
        """
        
        # Tombol Kirim WA & Cetak Nota bersebelahan
        col_wa, col_print = st.columns(2)
        with col_wa:
            st.link_button("📲 Kirim WA (081353539600)", link_wa, type="primary", use_container_width=True)
            
        with col_print:
            # Tombol print cerdas: Membuka window baru, mengisi struk, lalu menembak dialog cetak Chrome
            js_print_script = f"""
            <script>
            function cetakStruk() {{
                var printWindow = window.open('', '_blank');
                printWindow.document.write("<html><head><title>Print Nota KM QOLBIYA</title></head><body style='margin:10px;'>");
                printWindow.document.write(`{html_print_content}`);
                printWindow.document.write("</body></html>");
                printWindow.document.close();
                printWindow.focus();
                setTimeout(function() {{
                    printWindow.print();
                    printWindow.close();
                }}, 500);
            }}
            </script>
            <button onclick="cetakStruk()" style="width:100%; height:40px; background-color:#2563eb; color:white; border:none; border-radius:0.5rem; font-weight:bold; font-size:14px; cursor:pointer; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">
                🖨️ Print / Cetak Nota
            </button>
            """
            st.components.v1.html(js_print_script, height=45)
            
        st.markdown("---")
        if st.button("🔴 TUTUP BUKU & RESET SEMUA DATA", use_container_width=True):
            cursor = conn.cursor()
            cursor.execute("UPDATE perbekalan SET status='Lunas'")
            cursor.execute("DELETE FROM penjualan_ikan")
            conn.commit()
            st.success("Buku pelayaran ini ditutup! Semua kembali ke Rp 0.")
            st.rerun()

conn.close()
