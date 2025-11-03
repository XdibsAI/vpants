import pandas as pd

def calculate_profit(harga_jual, modal_pcs, jumlah, potongan_admin=3000, ongkos_jahit=0):
    total_modal = modal_pcs * jumlah
    profit = (harga_jual - total_modal) - potongan_admin - ongkos_jahit
    return profit

def calculate_admin_potongan(nominal_masuk, harga_jual):
    if harga_jual > 0:
        potongan = harga_jual - nominal_masuk
        persen = (potongan / harga_jual) * 100
        return potongan, persen
    return 0, 0
