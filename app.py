import streamlit as st
import pandas as pd
from utils.calculations import calculate_profit, calculate_admin_potongan
from utils.updates import update_stok, update_keuangan
from datetime import datetime
from fpdf import FPDF
import hashlib
import os

# Load data awal dengan penanganan file kosong
def load_or_init_df(file_path, columns):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=columns)

produk_df = load_or_init_df('config/produk.csv', ['Nama', 'Ukuran', 'Harga_Jual', 'Modal_Pcs', 'Isi_Pack', 'Bonus'])
transaksi_df = load_or_init_df('config/transaksi.csv', ['Jenis', 'Nominal', 'Tanggal', 'Catatan'])
stok_df = load_or_init_df('config/stok.csv', ['Jenis', 'Stok_Mentah', 'Stok_Jadi', 'Ukuran', 'Catatan'])
keuangan_df = load_or_init_df('config/keuangan.csv', ['Saldo_Berjalan', 'Total_Pemasukan', 'Total_Pengeluaran'])
users_df = load_or_init_df('config/users.csv', ['username', 'password'])

# Inisialisasi session state untuk autentikasi
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None

# Fungsi untuk hashing password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Halaman Login
if not st.session_state['authenticated']:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        user = users_df[users_df['username'] == username]
        if not user.empty and user['password'].iloc[0] == hash_password(password):
            st.session_state['authenticated'] = True
            st.session_state['current_user'] = username
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Username atau password salah!")

    st.stop()  # Hentikan eksekusi jika belum login

# Sidebar untuk Menu (hanya tampil setelah login)
st.sidebar.title("Menu")
menu = st.sidebar.radio("Pilih Menu", ["Dashboard", "Input Transaksi", "Laporan", "Riwayat Transaksi", "Pengaturan Produk", "Edit Stok", "Kelola Saldo", "Kelola Pengeluaran", "Ubah Password", "Logout"])

# Fungsi Logout
if menu == "Logout":
    st.session_state['authenticated'] = False
    st.session_state['current_user'] = None
    st.success("Anda telah logout!")
    st.rerun()

# Menu: Ubah Password
elif menu == "Ubah Password":
    st.header("Ubah Password")
    if st.session_state['current_user']:
        old_password = st.text_input("Password Lama", type="password")
        new_password = st.text_input("Password Baru", type="password")
        confirm_password = st.text_input("Konfirmasi Password Baru", type="password")
        change_button = st.button("Ubah Password")

        if change_button:
            # Verifikasi password lama
            current_user_data = users_df[users_df['username'] == st.session_state['current_user']]
            if not current_user_data.empty and current_user_data['password'].iloc[0] == hash_password(old_password):
                if new_password == confirm_password and new_password:
                    # Update password dengan hash baru
                    users_df.loc[users_df['username'] == st.session_state['current_user'], 'password'] = hash_password(new_password)
                    users_df.to_csv('config/users.csv', index=False)
                    st.success("Password berhasil diubah!")
                else:
                    st.error("Password baru dan konfirmasi tidak cocok atau kosong!")
            else:
                st.error("Password lama salah!")
    else:
        st.error("Silakan login terlebih dahulu!")

# Menu: Dashboard
elif menu == "Dashboard":
    st.header("Dashboard Utama")
    # Inisialisasi default jika keuangan_df kosong
    if keuangan_df.empty:
        saldo_utama = 0
        total_pemasukan = 0
        total_pengeluaran = 0
    else:
        saldo_utama = keuangan_df['Saldo_Berjalan'].iloc[0] if not pd.isna(keuangan_df['Saldo_Berjalan'].iloc[0]) else 0
        total_pemasukan = keuangan_df['Total_Pemasukan'].iloc[0] if not pd.isna(keuangan_df['Total_Pemasukan'].iloc[0]) else 0
        total_pengeluaran = keuangan_df['Total_Pengeluaran'].iloc[0] if not pd.isna(keuangan_df['Total_Pengeluaran'].iloc[0]) else 0
    st.metric(label="Saldo Utama", value=f"Rp {saldo_utama:,}")
    avg_modal_pcs = produk_df['Modal_Pcs'].mean() if not produk_df.empty else 0
    total_stok_jadi = stok_df[stok_df['Jenis'] == "Produk"]['Stok_Jadi'].sum() if not stok_df.empty else 0
    total_modal = avg_modal_pcs * total_stok_jadi
    saldo_profit = total_pemasukan - total_pengeluaran - total_modal
    st.metric(label="Saldo Profit", value=f"Rp {saldo_profit:,}")
    current_month = datetime.now().month
    pengeluaran_bulanan = transaksi_df[(transaksi_df['Jenis'] == "Pengeluaran") & 
                                      (pd.to_datetime(transaksi_df['Tanggal']).dt.month == current_month)]['Nominal'].sum() if not transaksi_df.empty else 0
    st.metric(label="Pengeluaran Bulanan", value=f"Rp {pengeluaran_bulanan:,}")
    st.subheader("Stok Keseluruhan")
    stok_produk = stok_df[stok_df['Jenis'] == "Produk"].groupby('Ukuran')['Stok_Jadi'].sum().reset_index() if not stok_df.empty else pd.DataFrame(columns=['Ukuran', 'Stok_Jadi'])
    stok_kemasan = stok_df[stok_df['Jenis'] == "Kemasan"].groupby('Ukuran')['Stok_Jadi'].sum().reset_index() if not stok_df.empty else pd.DataFrame(columns=['Ukuran', 'Stok_Jadi'])
    stok_lain_lain = stok_df[stok_df['Jenis'] == "Lain-lain"]['Stok_Jadi'].sum() if not stok_df.empty else 0
    st.write("### Stok Produk (per Ukuran)")
    st.dataframe(stok_produk)
    st.write("### Stok Kemasan (per Ukuran)")
    st.dataframe(stok_kemasan)
    st.write("### Stok Lain-lain")
    st.write(f"Total: {stok_lain_lain} pcs")
    def generate_csv_report():
        report_data = {"Saldo Utama": [saldo_utama], "Saldo Profit": [saldo_profit], "Pengeluaran Bulanan": [pengeluaran_bulanan], "Stok Produk": [stok_produk.to_dict() if not stok_produk.empty else {}], "Stok Kemasan": [stok_kemasan.to_dict() if not stok_kemasan.empty else {}], "Stok Lain-lain": [stok_lain_lain]}
        report_df = pd.DataFrame(report_data)
        return report_df.to_csv(index=False).encode('utf-8')
    def generate_pdf_report():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Laporan VPants - {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Saldo Utama: Rp {saldo_utama:,}", ln=True)
        pdf.cell(200, 10, txt=f"Saldo Profit: Rp {saldo_profit:,}", ln=True)
        pdf.cell(200, 10, txt=f"Pengeluaran Bulanan: Rp {pengeluaran_bulanan:,}", ln=True)
        pdf.ln(10)
        pdf.cell(200, 10, txt="Stok Produk:", ln=True)
        for index, row in stok_produk.iterrows():
            pdf.cell(200, 10, txt=f"Ukuran {row['Ukuran']}: {row['Stok_Jadi']} pcs", ln=True)
        pdf.ln(10)
        pdf.cell(200, 10, txt="Stok Kemasan:", ln=True)
        for index, row in stok_kemasan.iterrows():
            pdf.cell(200, 10, txt=f"Ukuran {row['Ukuran']}: {row['Stok_Jadi']} pcs", ln=True)
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Stok Lain-lain: {stok_lain_lain} pcs", ln=True)
        return pdf.output(dest="S").encode('latin1')
    st.download_button(label="Download Laporan CSV", data=generate_csv_report(), file_name=f"laporan_vpants_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    st.download_button(label="Download Laporan PDF", data=generate_pdf_report(), file_name=f"laporan_vpants_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")

# Menu: Input Transaksi
elif menu == "Input Transaksi":
    st.header("Input Transaksi")
    with st.form("input_transaksi"):
        jenis = st.selectbox("Jenis Transaksi", ["Penjualan", "Pembelian", "Pengeluaran"])
        nominal = st.number_input("Nominal", min_value=0)
        tanggal = st.date_input("Tanggal", value=datetime.now())
        catatan = st.text_input("Catatan")
        submit = st.form_submit_button("Submit")
        if submit:
            new_row = pd.DataFrame({"Jenis": [jenis], "Nominal": [nominal], "Tanggal": [tanggal], "Catatan": [catatan]})
            transaksi_df = pd.concat([transaksi_df, new_row], ignore_index=True)
            transaksi_df.to_csv('config/transaksi.csv', index=False)
            if jenis == "Penjualan":
                ukuran = st.selectbox("Ukuran", ["S", "M", "L", "XL", "XXL"])
                jumlah = st.number_input("Jumlah", min_value=1)
                # Jika produk_df kosong, gunakan input manual untuk harga dan modal sementara
                if produk_df.empty:
                    harga_jual = st.number_input("Harga Jual (sementara)", min_value=0)
                    modal_pcs = st.number_input("Modal per Pcs (sementara)", min_value=0)
                    profit = calculate_profit(harga_jual, modal_pcs, jumlah)
                else:
                    produk = produk_df[(produk_df['Ukuran'] == ukuran) & (produk_df['Isi_Pack'] == jumlah)].iloc[0]
                    profit = calculate_profit(produk['Harga_Jual'], produk['Modal_Pcs'], jumlah)
                keuangan_df = update_keuangan(keuangan_df, nominal, pemasukan=nominal)
                stok_df = update_stok(stok_df, "Produk", 0, -jumlah, ukuran)
            elif jenis == "Pembelian":
                keuangan_df = update_keuangan(keuangan_df, -nominal, pengeluaran=nominal)
                stok_df = update_stok(stok_df, "Bahan", nominal // 1000, 0, "-")
            elif jenis == "Pengeluaran":
                keuangan_df = update_keuangan(keuangan_df, -nominal, pengeluaran=nominal)
            stok_df.to_csv('config/stok.csv', index=False)
            keuangan_df.to_csv('config/keuangan.csv', index=False)
            st.success("Transaksi berhasil ditambahkan!")

# Menu: Laporan
elif menu == "Laporan":
    st.header("Laporan Keuangan & Stok")
    if keuangan_df.empty:
        st.write("Saldo Berjalan: Rp 0")
        st.write("Total Pemasukan: Rp 0")
        st.write("Total Pengeluaran: Rp 0")
    else:
        st.write("Saldo Berjalan:", keuangan_df['Saldo_Berjalan'].iloc[0] if not pd.isna(keuangan_df['Saldo_Berjalan'].iloc[0]) else 0)
        st.write("Total Pemasukan:", keuangan_df['Total_Pemasukan'].iloc[0] if not pd.isna(keuangan_df['Total_Pemasukan'].iloc[0]) else 0)
        st.write("Total Pengeluaran:", keuangan_df['Total_Pengeluaran'].iloc[0] if not pd.isna(keuangan_df['Total_Pengeluaran'].iloc[0]) else 0)
    st.write("Stok Tersedia:", stok_df if not stok_df.empty else "Tidak ada data stok")

# Menu: Riwayat Transaksi
elif menu == "Riwayat Transaksi":
    st.header("Riwayat Transaksi")
    st.dataframe(transaksi_df if not transaksi_df.empty else pd.DataFrame(columns=['Jenis', 'Nominal', 'Tanggal', 'Catatan']))

# Menu: Pengaturan Produk
elif menu == "Pengaturan Produk":
    st.header("Kelola Produk")
    st.dataframe(produk_df if not produk_df.empty else pd.DataFrame(columns=['Nama', 'Ukuran', 'Harga_Jual', 'Modal_Pcs', 'Isi_Pack', 'Bonus']))
    with st.form("update_produk"):
        nama = st.text_input("Nama Produk", value="VPants")
        ukuran = st.selectbox("Ukuran", ["S", "M", "L", "XL", "XXL"])
        harga_jual = st.number_input("Harga Jual", min_value=0)
        modal_pcs = st.number_input("Modal per Pcs", min_value=0)
        isi_pack = st.number_input("Isi per Pack", min_value=1)
        bonus = st.number_input("Bonus (Pcs)", min_value=0)
        submit_produk = st.form_submit_button("Tambah/Perbarui Produk")
        if submit_produk:
            new_product = pd.DataFrame({"Nama": [nama], "Ukuran": [ukuran], "Harga_Jual": [harga_jual], "Modal_Pcs": [modal_pcs], "Isi_Pack": [isi_pack], "Bonus": [bonus]})
            produk_df = pd.concat([produk_df, new_product], ignore_index=True)
            produk_df.to_csv('config/produk.csv', index=False)
            st.success("Produk berhasil ditambahkan/perbarui!")

# Menu: Edit Stok
elif menu == "Edit Stok":
    st.header("Edit atau Input Stok")
    kategori = st.selectbox("Pilih Kategori", ["Produk", "Kemasan", "Lain-lain"])
    if kategori == "Produk":
        ukuran = st.selectbox("Pilih Ukuran", ["S", "M", "L", "XL", "XXL"])
        stok_sekarang = stok_df[(stok_df['Jenis'] == "Produk") & (stok_df['Ukuran'] == ukuran)]['Stok_Jadi'].iloc[0] if not stok_df[(stok_df['Jenis'] == "Produk") & (stok_df['Ukuran'] == ukuran)].empty else 0
        action = st.radio("Aksi", ["Edit Stok", "Input Stok Manual"])
        if action == "Edit Stok":
            stok_baru = st.number_input("Stok Baru", min_value=0, value=stok_sekarang)
            catatan_stok = st.text_input("Catatan Stok", value="Perubahan manual")
            submit_stok = st.button("Simpan Perubahan")
            if submit_stok:
                if not stok_df[(stok_df['Jenis'] == "Produk") & (stok_df['Ukuran'] == ukuran)].empty:
                    stok_df.loc[(stok_df['Jenis'] == "Produk") & (stok_df['Ukuran'] == ukuran), 'Stok_Jadi'] = stok_baru
                else:
                    new_row = pd.DataFrame({"Jenis": ["Produk"], "Stok_Mentah": [0], "Stok_Jadi": [stok_baru], "Ukuran": [ukuran], "Catatan": [catatan_stok]})
                    stok_df = pd.concat([stok_df, new_row], ignore_index=True)
                stok_df.to_csv('config/stok.csv', index=False)
                st.success(f"Stok untuk ukuran {ukuran} diperbarui menjadi {stok_baru} dengan catatan: {catatan_stok}")
        elif action == "Input Stok Manual":
            stok_tambah = st.number_input("Jumlah Stok yang Ditambahkan", min_value=0)
            catatan_stok = st.text_input("Catatan Stok", value="Penambahan manual")
            submit_stok = st.button("Tambah Stok")
            if submit_stok:
                stok_baru = stok_sekarang + stok_tambah
                if not stok_df[(stok_df['Jenis'] == "Produk") & (stok_df['Ukuran'] == ukuran)].empty:
                    stok_df.loc[(stok_df['Jenis'] == "Produk") & (stok_df['Ukuran'] == ukuran), 'Stok_Jadi'] = stok_baru
                else:
                    new_row = pd.DataFrame({"Jenis": ["Produk"], "Stok_Mentah": [0], "Stok_Jadi": [stok_baru], "Ukuran": [ukuran], "Catatan": [catatan_stok]})
                    stok_df = pd.concat([stok_df, new_row], ignore_index=True)
                stok_df.to_csv('config/stok.csv', index=False)
                st.success(f"Stok untuk ukuran {ukuran} ditambahkan {stok_tambah}, total menjadi {stok_baru} dengan catatan: {catatan_stok}")
    elif kategori == "Kemasan":
        ukuran = st.selectbox("Pilih Ukuran", ["S", "M", "L", "XL", "XXL"])
        stok_sekarang = stok_df[(stok_df['Jenis'] == "Kemasan") & (stok_df['Ukuran'] == ukuran)]['Stok_Jadi'].iloc[0] if not stok_df[(stok_df['Jenis'] == "Kemasan") & (stok_df['Ukuran'] == ukuran)].empty else 0
        action = st.radio("Aksi", ["Edit Stok", "Input Stok Manual"])
        if action == "Edit Stok":
            stok_baru = st.number_input("Stok Baru", min_value=0, value=stok_sekarang)
            catatan_stok = st.text_input("Catatan Stok", value="Perubahan kemasan manual")
            submit_stok = st.button("Simpan Perubahan")
            if submit_stok:
                if not stok_df[(stok_df['Jenis'] == "Kemasan") & (stok_df['Ukuran'] == ukuran)].empty:
                    stok_df.loc[(stok_df['Jenis'] == "Kemasan") & (stok_df['Ukuran'] == ukuran), 'Stok_Jadi'] = stok_baru
                else:
                    new_row = pd.DataFrame({"Jenis": ["Kemasan"], "Stok_Mentah": [0], "Stok_Jadi": [stok_baru], "Ukuran": [ukuran], "Catatan": [catatan_stok]})
                    stok_df = pd.concat([stok_df, new_row], ignore_index=True)
                stok_df.to_csv('config/stok.csv', index=False)
                st.success(f"Stok kemasan untuk ukuran {ukuran} diperbarui menjadi {stok_baru} dengan catatan: {catatan_stok}")
        elif action == "Input Stok Manual":
            stok_tambah = st.number_input("Jumlah Stok yang Ditambahkan", min_value=0)
            catatan_stok = st.text_input("Catatan Stok", value="Penambahan kemasan manual")
            submit_stok = st.button("Tambah Stok")
            if submit_stok:
                stok_baru = stok_sekarang + stok_tambah
                if not stok_df[(stok_df['Jenis'] == "Kemasan") & (stok_df['Ukuran'] == ukuran)].empty:
                    stok_df.loc[(stok_df['Jenis'] == "Kemasan") & (stok_df['Ukuran'] == ukuran), 'Stok_Jadi'] = stok_baru
                else:
                    new_row = pd.DataFrame({"Jenis": ["Kemasan"], "Stok_Mentah": [0], "Stok_Jadi": [stok_baru], "Ukuran": [ukuran], "Catatan": [catatan_stok]})
                    stok_df = pd.concat([stok_df, new_row], ignore_index=True)
                stok_df.to_csv('config/stok.csv', index=False)
                st.success(f"Stok kemasan untuk ukuran {ukuran} ditambahkan {stok_tambah}, total menjadi {stok_baru} dengan catatan: {catatan_stok}")
    elif kategori == "Lain-lain":
        catatan_stok = st.text_input("Catatan Stok Lain-lain", value="Stok acak")
        stok_tambah = st.number_input("Jumlah Stok yang Ditambahkan", min_value=0)
        submit_stok = st.button("Tambah Stok Lain-lain")
        if submit_stok:
            new_row = pd.DataFrame({"Jenis": ["Lain-lain"], "Stok_Mentah": [0], "Stok_Jadi": [stok_tambah], "Ukuran": ["-"], "Catatan": [catatan_stok]})
            stok_df = pd.concat([stok_df, new_row], ignore_index=True)
            stok_df.to_csv('config/stok.csv', index=False)
            st.success(f"Stok lain-lain ditambahkan {stok_tambah} dengan catatan: {catatan_stok}")

# Menu: Kelola Saldo
elif menu == "Kelola Saldo":
    st.header("Kelola Saldo")
    if keuangan_df.empty:
        saldo_sekarang = 0
    else:
        saldo_sekarang = keuangan_df['Saldo_Berjalan'].iloc[0] if not pd.isna(keuangan_df['Saldo_Berjalan'].iloc[0]) else 0
    action = st.radio("Aksi", ["Tambah Saldo", "Kurangi Saldo", "Set Saldo Baru"])
    if action == "Tambah Saldo":
        tambah_saldo = st.number_input("Jumlah yang Ditambahkan", min_value=0)
        catatan_saldo = st.text_input("Catatan Saldo", value="Penambahan manual")
        submit_saldo = st.button("Tambah Saldo")
        if submit_saldo:
            keuangan_df = update_keuangan(keuangan_df, tambah_saldo, pemasukan=tambah_saldo)
            new_row = pd.DataFrame({"Jenis": ["Pemasukan"], "Nominal": [tambah_saldo], "Tanggal": [datetime.now()], "Catatan": [catatan_saldo]})
            transaksi_df = pd.concat([transaksi_df, new_row], ignore_index=True)
            transaksi_df.to_csv('config/transaksi.csv', index=False)
            keuangan_df.to_csv('config/keuangan.csv', index=False)
            st.success(f"Saldo ditambahkan {tambah_saldo}, total menjadi {keuangan_df['Saldo_Berjalan'].iloc[0]} dengan catatan: {catatan_saldo}")
    elif action == "Kurangi Saldo":
        kurangi_saldo = st.number_input("Jumlah yang Dikurangi", min_value=0, max_value=saldo_sekarang)
        catatan_saldo = st.text_input("Catatan Saldo", value="Pengurangan manual")
        submit_saldo = st.button("Kurangi Saldo")
        if submit_saldo:
            keuangan_df = update_keuangan(keuangan_df, -kurangi_saldo, pengeluaran=kurangi_saldo)
            new_row = pd.DataFrame({"Jenis": ["Pengeluaran"], "Nominal": [kurangi_saldo], "Tanggal": [datetime.now()], "Catatan": [catatan_saldo]})
            transaksi_df = pd.concat([transaksi_df, new_row], ignore_index=True)
            transaksi_df.to_csv('config/transaksi.csv', index=False)
            keuangan_df.to_csv('config/keuangan.csv', index=False)
            st.success(f"Saldo dikurangi {kurangi_saldo}, total menjadi {keuangan_df['Saldo_Berjalan'].iloc[0]} dengan catatan: {catatan_saldo}")
    elif action == "Set Saldo Baru":
        saldo_baru = st.number_input("Saldo Baru", min_value=0)
        catatan_saldo = st.text_input("Catatan Saldo", value="Set ulang manual")
        submit_saldo = st.button("Set Saldo")
        if submit_saldo:
            perubahan = saldo_baru - saldo_sekarang
            keuangan_df = update_keuangan(keuangan_df, perubahan)
            new_row = pd.DataFrame({"Jenis": ["Penyesuaian"], "Nominal": [abs(perubahan)], "Tanggal": [datetime.now()], "Catatan": [catatan_saldo]})
            transaksi_df = pd.concat([transaksi_df, new_row], ignore_index=True)
            transaksi_df.to_csv('config/transaksi.csv', index=False)
            keuangan_df.to_csv('config/keuangan.csv', index=False)
            st.success(f"Saldo diset menjadi {saldo_baru} dengan catatan: {catatan_saldo}")

# Menu: Kelola Pengeluaran
elif menu == "Kelola Pengeluaran":
    st.header("Kelola Pengeluaran")
    if keuangan_df.empty:
        saldo_sekarang = 0
    else:
        saldo_sekarang = keuangan_df['Saldo_Berjalan'].iloc[0] if not pd.isna(keuangan_df['Saldo_Berjalan'].iloc[0]) else 0
    nominal_pengeluaran = st.number_input("Nominal Pengeluaran", min_value=0)
    catatan_pengeluaran = st.text_input("Catatan Pengeluaran", value="Pengeluaran manual")
    submit_pengeluaran = st.button("Simpan Pengeluaran")
    if submit_pengeluaran:
        if nominal_pengeluaran <= saldo_sekarang:
            keuangan_df = update_keuangan(keuangan_df, -nominal_pengeluaran, pengeluaran=nominal_pengeluaran)
            new_row = pd.DataFrame({"Jenis": ["Pengeluaran"], "Nominal": [nominal_pengeluaran], "Tanggal": [datetime.now()], "Catatan": [catatan_pengeluaran]})
            transaksi_df = pd.concat([transaksi_df, new_row], ignore_index=True)
            transaksi_df.to_csv('config/transaksi.csv', index=False)
            keuangan_df.to_csv('config/keuangan.csv', index=False)
            st.success(f"Pengeluaran {nominal_pengeluaran} berhasil dicatat, saldo tersisa: {keuangan_df['Saldo_Berjalan'].iloc[0]} dengan catatan: {catatan_pengeluaran}")
        else:
            st.error("Saldo tidak mencukupi untuk pengeluaran ini!")

# Simpan perubahan
transaksi_df.to_csv('config/transaksi.csv', index=False)
stok_df.to_csv('config/stok.csv', index=False)
keuangan_df.to_csv('config/keuangan.csv', index=False)
