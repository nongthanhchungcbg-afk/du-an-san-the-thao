# -*- coding: utf-8 -*-
import sys
import sqlite3

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def view_available_pitches():
    try:
        conn = sqlite3.connect("sports_pitch.db")
        cur = conn.cursor()
        cur.execute("SELECT id, name, sport_type, price_per_hour, status FROM pitches WHERE status = 'AVAILABLE'")
        rows = cur.fetchall()
        
        print("=" * 80)
        print("        DANH SÁCH SÂN THỂ THAO ĐANG TRỐNG TRONG CSDL (AVAILABLE)        ")
        print("=" * 80)
        print(f"{'ID':<4} | {'TÊN SÂN':<42} | {'MÔN':<10} | {'GIÁ THUÊ':<12} | {'TRẠNG THÁI'}")
        print("-" * 80)
        for r in rows:
            sport = str(r[2]).replace('PitchType.', '')
            price = f"{int(r[3]):,}".replace(',', '.') + " đ"
            print(f"{r[0]:<4} | {r[1]:<42} | {sport:<10} | {price:<12} | {r[4]}")
        print("=" * 80)
        print(f"👉 TỔNG SỐ SÂN ĐANG SẴN SÀNG HOẠT ĐỘNG: {len(rows)} SÂN")
        print("=" * 80)
        conn.close()
    except Exception as e:
        print("Lỗi truy vấn:", e)

if __name__ == "__main__":
    view_available_pitches()
