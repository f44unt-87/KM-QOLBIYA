        # 2. STRUKTUR NOTA PRINT BERWARNA (Sempurna untuk Dark Mode & Light Mode)
        html_print_content = f"""
        <div style='font-family: Arial, sans-serif; max-width: 500px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background-color: #ffffff; color: #000000;'>
            <h2 style='color: #1e3a8a; text-align: center; margin-bottom: 5px;'>⚓ KM QOLBIYA</h2>
            <p style='text-align: center; color: #444444; font-size: 12px; margin-top: 0;'>Laporan Totalan Hasil Layar - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            
            <table style='width: 100%; border-collapse: collapse; margin-top: 15px;'>
                <thead>
                    <tr style='background-color: #3b82f6; color: #ffffff; text-align: left; font-size: 13px;'>
                        <th style='padding: 10px; border: 1px solid #cbd5e1; color: #ffffff;'>Tanggal</th>
                        <th style='padding: 10px; border: 1px solid #cbd5e1; color: #ffffff;'>Keterangan Bon</th>
                        <th style='padding: 10px; border: 1px solid #cbd5e1; text-align: right; color: #ffffff;'>Nominal</th>
                    </tr>
                </thead>
                <tbody style='font-size: 13px;'>
        """
        for idx, r in edited_df.iterrows():
            bg_row = "#f8fafc" if idx % 2 == 0 else "#ffffff"
            html_print_content += f"""
                    <tr style='background-color: {bg_row}; color: #000000;'>
                        <td style='padding: 10px; border: 1px solid #e2e8f0; color: #333333;'>{r['Tanggal']}</td>
                        <td style='padding: 10px; border: 1px solid #e2e8f0; font-weight: bold; color: #000000;'>{r['Keterangan Bon']}</td>
                        <td style='padding: 10px; border: 1px solid #e2e8f0; text-align: right; color: #b91c1c; font-weight: bold;'>Rp {r['Nominal (Rp)']:,.0f}</td>
                    </tr>
            """
        html_print_content += f"""
                </tbody>
            </table>
            
            <table style='width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; font-weight: bold;'>
                <tr style='background-color: #fca5a5; color: #991b1b;'>
                    <td style='padding: 10px; border: 1px solid #f87171; color: #991b1b;'>📦 TOTAL BON PERBEKALAN</td>
                    <td style='padding: 10px; border: 1px solid #f87171; text-align: right; color: #991b1b;'>Rp {total_perbekalan:,.0f}</td>
                </tr>
                <tr style='background-color: #86efac; color: #166534;'>
                    <td style='padding: 10px; border: 1px solid #4ade80; color: #166534;'>💰 PENDAPATAN KOTOR LAUT</td>
                    <td style='padding: 10px; border: 1px solid #4ade80; text-align: right; color: #166534;'>Rp {total_pendapatan_kotor:,.0f}</td>
                </tr>
                <tr style='background-color: #1e3a8a; color: #ffffff; font-size: 15px;'>
                    <td style='padding: 12px; border: 1px solid #1e3a8a; color: #ffffff;'>💵 SISA BERSIH (BAGI HASIL)</td>
                    <td style='padding: 12px; border: 1px solid #1e3a8a; text-align: right; font-weight: 900; color: #ffffff;'>Rp {sisa_原始:,.0f}</td>
                </tr>
            </table>
            <p style='text-align: center; font-size: 11px; color: #64748b; margin-top: 25px;'><i>Sistem Catatan Kasir Resmi - MasdabiyaNet</i></p>
        </div>
        """
