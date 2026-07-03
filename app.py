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
st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'>Sistem Manajemen Hasil Berlayar</p>", unsafe_allow_html=True)

def get_connection():
    return sqlite3.connect("database_qolbiya.db")

conn = get_connection()

# AMBIL DATA UNTUK KALKULASI TOTALAN
total_perbekalan = pd.read_sql_query("SELECT SUM(nominal) FROM perbekalan WHERE status='Belum Lunas'", conn).iloc[0,0] or 0
total_pendapatan_kotor = pd.read_sql_query("SELECT SUM(pendapatan_kotor) FROM penjualan_ikan", conn).iloc[0,0] or 0
sisa_bersih = total_pendapatan_kotor - total_perbekalan

# --- MEMBUAT 4 TAB ---
tab1, tab2, tab3, tab4 = st.tabs(["🛒 Input Bon", "🐟 Input Jual Ikan", "📋 Laporan Totalan", "👥 Bagi Hasil ABK"])

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

# ==================== TAB 3: LAPORAN, EDIT, & NOTA BERWARNA ====================
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
        
        # 1. GENERATE RINCIAN DATA BON UNTUK WA
        rincian_wa_items = ""
        for _, r in edited_df.iterrows():
            rincian_wa_items += f"- {r['Keterangan Bon']}: Rp {r['Nominal (Rp)']:,.0f}\n"

        text_wa = (
            f"*⚓ NOTA TOTALAN KM QOLBIYA*\n"
            f"Tanggal: {datetime.now().strftime('%d-%m-%Y %H:%M')}\n\n"
            f"*Rincian Pengeluaran Bon:*\n"
            f"{rincian_wa_items}"
            f"\n----------------------------------------\n"
            f"📦 *Total Bon:* Rp {total_perbekalan:,.0f}\n"
            f"💰 *Pendapatan Kotor:* Rp {total_pendapatan_kotor:,.0f}\n"
            f"💵 *SISA BERSIH:* Rp {sisa_bersih:,.0f}\n"
            f"----------------------------------------\n"
            f"_Sistem Catatan MasdabiyaNet_"
        )
        
        encoded_text = urllib.parse.quote(text_wa)
        link_wa = f"https://wa.me/6281353539600?text={encoded_text}"
        
        # 2. STRUKTUR NOTA PRINT BERWARNA
        html_print_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background-color: #ffffff; color: #000000;">
            <h2 style="color: #1e3a8a; text-align: center; margin-bottom: 5px;">&#9875; KM QOLBIYA</h2>
            <p style="text-align: center; color: #000000; font-size: 12px; margin-top: 0; font-weight: bold;">Laporan Totalan Hasil Berlayar - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #3b82f6; color: #ffffff; text-align: left; font-size: 13px;">
                        <th style="padding: 10px; border: 1px solid #cbd5e1; color: #ffffff;">Tanggal</th>
                        <th style="padding: 10px; border: 1px solid #cbd5e1; color: #ffffff;">Keterangan Bon</th>
                        <th style="padding: 10px; border: 1px solid #cbd5e1; text-align: right; color: #ffffff;">Nominal</th>
                    </tr>
                </thead>
                <tbody style="font-size: 13px;">
        """
        for idx, r in edited_df.iterrows():
            bg_row = "#f8fafc" if idx % 2 == 0 else "#ffffff"
            html_print_content += f"""
                    <tr style="background-color: {bg_row}; color: #000000;">
                        <td style="padding: 10px; border: 1px solid #e2e8f0; color: #000000; font-weight: bold;">{r['Tanggal']}</td>
                        <td style="padding: 10px; border: 1px solid #e2e8f0; font-weight: bold; color: #000000;">{r['Keterangan Bon']}</td>
                        <td style="padding: 10px; border: 1px solid #e2e8f0; text-align: right; color: #000000; font-weight: bold;">Rp {r['Nominal (Rp)']:,.0f}</td>
                    </tr>
            """
        html_print_content += f"""
                </tbody>
            </table>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; font-weight: bold;">
                <tr style="background-color: #fca5a5; color: #000000;">
                    <td style="padding: 10px; border: 1px solid #f87171; color: #000000;">&#128230; TOTAL BON PERBEKALAN</td>
                    <td style="padding: 10px; border: 1px solid #f87171; text-align: right; color: #000000; font-weight: bold;">Rp {total_perbekalan:,.0f}</td>
                </tr>
                <tr style="background-color: #86efac; color: #000000;">
                    <td style="padding: 10px; border: 1px solid #4ade80; color: #000000;">&#128176; PENDAPATAN KOTOR LAUT</td>
                    <td style="padding: 10px; border: 1px solid #4ade80; text-align: right; color: #000000; font-weight: bold;">Rp {total_pendapatan_kotor:,.0f}</td>
                </tr>
                <tr style="background-color: #1e3a8a; color: #ffffff; font-size: 15px;">
                    <td style="padding: 12px; border: 1px solid #1e3a8a; color: #ffffff;">&#128181; SISA BERSIH (BAGI HASIL)</td>
                    <td style="padding: 12px; border: 1px solid #1e3a8a; text-align: right; font-weight: 900; color: #ffffff;">Rp {sisa_bersih:,.0f}</td>
                </tr>
            </table>
            <p style="text-align: center; font-size: 11px; color: #64748b; margin-top: 25px; font-weight: bold;"><i>Sistem Catatan Kasir Resmi - MasdabiyaNet</i></p>
        </div>
        """
        
        # Tombol Kirim WA & Cetak Nota Bersebelahan
        col_wa, col_print = st.columns(2)
        with col_wa:
            st.link_button("📲 Kirim WA (081353539600)", link_wa, type="primary", use_container_width=True)
            
        with col_print:
            js_print_script = f"""
            <script>
            function cetakStruk() {{
                var printWindow = window.open('', '_blank');
                printWindow.document.write("<html><head><title>Print Nota KM QOLBIYA</title></head><body>");
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
            <button onclick="cetakStruk()" style="width:100%; height:40px; background-color:#2563eb; color:white; border:none; border-radius:0.5rem; font-weight:bold; font-size:14px; cursor:pointer;">
                🖨️ Print / Cetak Nota
            </button>
            """
            st.components.v1.html(js_print_script, height=45)
            
        st.markdown("---")
        if st.button("🔴 TUTUP BUKU & RESET SEMUA DATA", use_container_width=True, key="reset_tab3"):
            cursor = conn.cursor()
            cursor.execute("UPDATE perbekalan SET status='Lunas'")
            cursor.execute("DELETE FROM penjualan_ikan")
            conn.commit()
            st.success("Buku pelayaran ini ditutup! Semua kembali ke Rp 0.")
            st.rerun()

# ==================== TAB 4: BAGI HASIL ABK ====================
with tab4:
    st.markdown("### 👥 Perhitungan Pembagian Hasil ABK")
    
    if sisa_bersih <= 0:
        st.warning("Belum ada Sisa Bersih / Hasil Jual Ikan untuk dihitung bagi hasilnya.")
    else:
        # LOGIKA PERHITUNGAN AWAL (REFERENSI SAJA)
        hasil_referensi = sisa_bersih / 76
        
        st.info(f"💵 **Laba Bersih Perjalanan:** Rp {sisa_bersih:,.0f}")
        st.caption(f"💡 Referensi Hitungan Pokok (Laba / 76): Rp {hasil_referensi:,.2f}")
        
        # INPUT MANUAL SESUAI KEINGINAN BOS KANKER
        st.markdown("---")
        hasil_olah = st.number_input(
            "✍️ **Masukkan Hasil Olah (Sesuai Keinginan Anda):**", 
            min_value=0, 
            value=int((sisa_bersih / 76) // 100000) * 100000 if sisa_bersih > 0 else 0,
            step=50000,
            help="Isi manual angka pembulatan yang Anda inginkan di sini."
        )
        
        # Hitung Jatah Berdasarkan Input Manual
        kapal = 30 * hasil_olah
        seluruh_abk = 36 * hasil_olah
        spesial_abk = 10 * hasil_olah  # Juru mudi/mesin/prapen
        per_abk = 2 * hasil_olah       # Info jatah per orang ABK
        
        # Hitung Sisa Dana Setelah Dibagikan ke 3 Pos Utama
        total_dibagikan = kapal + seluruh_abk + spesial_abk
        sisa_dana_cadangan = sisa_bersih - total_dibagikan
        
        st.markdown("---")
        st.markdown("#### 📋 Rincian Distribusi Uang:")
        
        # Tampilan tabel hasil input manual
        data_pembagian = {
            "Penerima / Pos": [
                "🚢 1. Penghasilan Kapal (30x)",
                "👨‍👩‍👦 2. Penghasilan Seluruh ABK (36x)",
                "🔧 3. Penghasilan Juru Mudi / Mesin / Prapen (10x)",
                "🐟 Jatah Bersih per Individu ABK (2x)"
            ],
            "Total Uang Dibayar": [
                f"Rp {kapal:,.0f}",
                f"Rp {seluruh_abk:,.0f}",
                f"Rp {spesial_abk:,.0f}",
                f"Rp {per_abk:,.0f}"
            ]
        }
        df_pembagian = pd.DataFrame(data_pembagian)
        st.dataframe(df_pembagian, use_container_width=True, hide_index=True)
        
        # TAMPILAN SISA KAS SETELAH DIBAGIKAN
        if sisa_dana_cadangan >= 0:
            st.success(f"📈 **Sisa Uang (Masuk Kas/Cadangan Kapal):** Rp {sisa_dana_cadangan:,.0f}")
        else:
            st.danger(f"📉 **Minus (Uang Dibagi Melebihi Laba Bersih):** Rp {sisa_dana_cadangan:,.0f}")
            
        st.markdown("---")
        # GENERATE TEKS WA LAPORAN MANUAL
        text_wa_bagi = (
            f"*👥 LAPORAN BAGI HASIL KM QOLBIYA*\n"
            f"Tanggal: {datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
            f"Laba Bersih Perjalanan: Rp {sisa_bersih:,.0f}\n"
            f"Nilai Hasil Olah (Manual): Rp {hasil_olah:,.0f}\n"
            f"----------------------------------------\n"
            f"🚢 *Penghasilan Kapal (30x):* Rp {kapal:,.0f}\n"
            f"👨‍👩‍👦 *Penghasilan Seluruh ABK (36x):* Rp {seluruh_abk:,.0f}\n"
            f"🔧 *Juru Mudi/Mesin/Prapen (10x):* Rp {spesial_abk:,.0f}\n"
            f"🐟 *Penghasilan Per ABK (2x):* Rp {per_abk:,.0f}\n"
            f"----------------------------------------\n"
            f"💰 *SISA KAS / CADANGAN:* Rp {sisa_dana_cadangan:,.0f}\n"
            f"----------------------------------------\n"
            f"_Sistem Catatan MasdabiyaNet_"
        )
        encoded_wa_bagi = urllib.parse.quote(text_wa_bagi)
        link_wa_bagi = f"https://wa.me/6281353539600?text={encoded_wa_bagi}"
        
        st.link_button("📲 Kirim WA Laporan ABK (081353539600)", link_wa_bagi, type="primary", use_container_width=True)

conn.close()
