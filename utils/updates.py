import pandas as pd

def update_stok(stok_df, jenis, stok_mentah, stok_jadi, ukuran):
    if jenis == "Bahan":
        stok_df.loc[stok_df['Jenis'] == "Bahan", 'Stok_Mentah'] += stok_mentah
    elif jenis == "Produk":
        mask = (stok_df['Jenis'] == "Produk") & (stok_df['Ukuran'] == ukuran)
        stok_df.loc[mask, 'Stok_Jadi'] += stok_jadi
    return stok_df

def update_keuangan(keuangan_df, saldo_change, pemasukan=0, pengeluaran=0):
    keuangan_df.loc[0, 'Saldo_Berjalan'] += saldo_change
    keuangan_df.loc[0, 'Total_Pemasukan'] += pemasukan
    keuangan_df.loc[0, 'Total_Pengeluaran'] += pengeluaran
    return keuangan_df
