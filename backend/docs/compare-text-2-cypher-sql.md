Mọi câu hỏi analytical đều có dạng này
```
SELECT [dimension columns], SUM/COUNT/AVG(measure)
FROM fact_table
JOIN dim_x ...
WHERE [filter]
GROUP BY [dimension columns]
```

Nếu dùng Text-to-SQL trên **database gốc (OLTP)**, LLM phải tự xử lý:
- Join 5-6 bảng normalized
- Tự tính toán aggregation từ raw data
- Hiểu được foreign key cross-schema
- Dễ ra kết quả sai mà không báo lỗi

Fact + Dimension đã **pre-aggregate và denormalize** rồi — LLM chỉ cần JOIN ít bảng hơn, ít sai hơn.

---

## Text-to-Cypher → hợp với database gốc hơn

**Lý do:** Graph database shine khi data có **quan hệ phức tạp nhiều bậc** — đúng cái OLTP có. OLTP là mạng lưới quan hệ tự nhiên:
```
(KhachHang)-[:SONG_O]->(ThanhPho)-[:THUOC]->(Bang)
(KhachHang)-[:DAT]->(DonHang)-[:CHUA]->(MatHang)
(MatHang)-[:LUU_TAI]->(CuaHang)-[:THUOC]->(ThanhPho)
```

Câu hỏi kiểu *"tìm khách hàng sống ở thành phố có cửa hàng đang bán mặt hàng họ đã đặt"* — trong SQL cần 4 JOIN, trong Cypher chỉ cần traverse graph tự nhiên.

Còn nếu dùng Text-to-Cypher trên Fact + Dimension thì **lãng phí** — Star Schema vốn đã flat, không có quan hệ phức tạp để graph tỏa sáng.

---

## Tóm lại bảng đối chiếu
```
                    OLTP (database gốc)     Fact + Dimension
                    ───────────────────     ────────────────
Text-to-SQL         ❌ Khó, nhiều JOIN       ✅ Pattern đơn giản
                    dễ sai, cross-schema     consistent, ít sai

Text-to-Cypher      ✅ Tự nhiên, traverse    ❌ Lãng phí
                    quan hệ nhiều bậc        Star Schema đã flat
                    không cần JOIN           không cần graph
```

---

## Trong thực tế người ta làm thế nào?

Các hệ thống production thường dùng **cả hai tầng**:
```
Câu hỏi người dùng
        ↓
    Router (LLM phân loại câu hỏi)
        ├── "Doanh thu tháng 3?"        → Text-to-SQL → DW (Fact+Dim)
        ├── "KH nào liên quan đến...?"  → Text-to-Cypher → Graph (OLTP)
        └── "Chính sách hoàn trả?"      → Vector Search → Doc store