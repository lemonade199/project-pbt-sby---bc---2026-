"""
midtrans_snap.py - Helper membuat transaksi Midtrans Snap
Aplikasi Business Center SMKN 13 Bandung
"""

import midtransclient
from midtrans_config import (
    MIDTRANS_SERVER_KEY, MIDTRANS_CLIENT_KEY,
    MIDTRANS_IS_PRODUCTION, ENABLED_PAYMENTS,
    WEBHOOK_BASE,
)


def create_snap_transaction(
    id_pesanan: int,
    total: float,
    nama_pembeli: str = "Pembeli",
    items: list = None,
) -> str:
    """
    Buat transaksi Midtrans Snap, kembalikan snap_token.

    Parameters:
        id_pesanan   : ID pesanan di tabel pesanan
        total        : Total harga (float)
        nama_pembeli : Nama pembeli (opsional)
        items        : List of dict {id, price, quantity, name}

    Returns:
        snap_token: str

    Raises:
        Exception jika Midtrans menolak request
    """
    snap = midtransclient.Snap(
        is_production=MIDTRANS_IS_PRODUCTION,
        server_key=MIDTRANS_SERVER_KEY,
        client_key=MIDTRANS_CLIENT_KEY,
    )

    order_id = f"BC-{id_pesanan}"

    # Default item jika tidak ada detail
    if not items:
        items = [{
            "id": f"pesanan-{id_pesanan}",
            "price": int(total),
            "quantity": 1,
            "name": f"Pesanan BC #{id_pesanan}",
        }]

    param = {
        "transaction_details": {
            "order_id": order_id,
            "gross_amount": int(total),
        },
        "customer_details": {
            "first_name": nama_pembeli,
        },
        "item_details": items,
        "enabled_payments": ENABLED_PAYMENTS,
        "callbacks": {
            "finish": f"{WEBHOOK_BASE}/pay/finish",
        },
    }

    transaction = snap.create_transaction(param)
    return transaction["token"]
