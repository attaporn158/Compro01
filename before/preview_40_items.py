"""สร้างไฟล์ตัวอย่างสินค้า 40 รายการสำหรับตรวจดูรูปแบบเท่านั้น."""

from pathlib import Path
import unicodedata


OUTPUT_FILE = Path(__file__).resolve().parent / "item_preview_40.txt"

ITEMS = [
    (1001, "เครื่องเขียน", "ปากกาลูกลื่นสีน้ำเงิน", "ด้าม", 50, 12.00),
    (1002, "เครื่องเขียน", "ปากกาลูกลื่นสีดำ", "ด้าม", 50, 12.00),
    (1003, "เครื่องเขียน", "ดินสอ 2B", "แท่ง", 50, 8.00),
    (1004, "เครื่องเขียน", "ยางลบ", "ก้อน", 50, 10.00),
    (1005, "เครื่องเขียน", "กบเหลาดินสอ", "อัน", 50, 15.00),
    (1006, "เครื่องเขียน", "ปากกาเน้นข้อความ", "ด้าม", 50, 25.00),
    (1007, "เครื่องเขียน", "ไม้บรรทัด 30 ซม.", "อัน", 50, 18.00),
    (1008, "เครื่องเขียน", "สมุดโน้ต A5", "เล่ม", 50, 35.00),
    (1009, "เครื่องเขียน", "กระดาษถ่ายเอกสาร A4", "รีม", 50, 125.00),
    (1010, "เครื่องเขียน", "ลิควิดเทป", "อัน", 50, 30.00),
    (1011, "ของทั่วไป", "กระดาษทิชชู", "ห่อ", 50, 25.00),
    (1012, "ของทั่วไป", "กล่องใส่เอกสาร", "กล่อง", 50, 65.00),
    (1013, "ของทั่วไป", "แฟ้มใส A4", "เล่ม", 50, 20.00),
    (1014, "ของทั่วไป", "คลิปหนีบกระดาษ", "กล่อง", 50, 35.00),
    (1015, "ของทั่วไป", "เทปใส", "ม้วน", 50, 22.00),
    (1016, "ของทั่วไป", "กรรไกร", "อัน", 50, 45.00),
    (1017, "ของทั่วไป", "คัตเตอร์", "อัน", 50, 30.00),
    (1018, "ของทั่วไป", "กระดาษโน้ตกาว", "แพ็ก", 50, 40.00),
    (1019, "ของทั่วไป", "ถ่าน AA", "แพ็ก", 50, 85.00),
    (1020, "ของทั่วไป", "ถ่าน AAA", "แพ็ก", 50, 85.00),
    (1021, "อุปกรณ์", "สาย USB-A to USB-C 1 เมตร", "เส้น", 50, 99.00),
    (1022, "อุปกรณ์", "สาย USB-A to USB-C 2 เมตร", "เส้น", 50, 149.00),
    (1023, "อุปกรณ์", "สาย USB-C to USB-C 1 เมตร", "เส้น", 50, 179.00),
    (1024, "อุปกรณ์", "สาย USB-C to USB-C 2 เมตร", "เส้น", 50, 249.00),
    (1025, "อุปกรณ์", "สาย USB-A to Lightning 1 เมตร", "เส้น", 50, 199.00),
    (1026, "อุปกรณ์", "สาย USB-C to Lightning 1 เมตร", "เส้น", 50, 299.00),
    (1027, "อุปกรณ์", "สาย Micro-USB 1 เมตร", "เส้น", 50, 79.00),
    (1028, "อุปกรณ์", "สายชาร์จแม่เหล็ก USB-C", "เส้น", 50, 189.00),
    (1029, "อุปกรณ์", "สายชาร์จนาฬิกาอัจฉริยะ", "เส้น", 50, 259.00),
    (1030, "อุปกรณ์", "สายชาร์จ 3 หัว", "เส้น", 50, 159.00),
    (1031, "อุปกรณ์", "หูฟังมีสายหัว 3.5 มม.", "ชิ้น", 50, 199.00),
    (1032, "อุปกรณ์", "หูฟังมีสายหัว USB-C", "ชิ้น", 50, 299.00),
    (1033, "อุปกรณ์", "หูฟังมีสายหัว Lightning", "ชิ้น", 50, 399.00),
    (1034, "อุปกรณ์", "หูฟังไร้สายแบบอินเอียร์", "คู่", 50, 690.00),
    (1035, "อุปกรณ์", "หูฟังไร้สายแบบครอบหู", "ชิ้น", 50, 1290.00),
    (1036, "อุปกรณ์", "หูฟังแบบเอียร์บัด", "คู่", 50, 590.00),
    (1037, "อุปกรณ์", "หูฟังเกมมิงมีไมโครโฟน", "ชิ้น", 50, 990.00),
    (1038, "อุปกรณ์", "หูฟังครอบหูแบบมีสาย", "ชิ้น", 50, 750.00),
    (1039, "อุปกรณ์", "หูฟังบลูทูธแบบคล้องคอ", "ชิ้น", 50, 850.00),
    (1040, "อุปกรณ์", "หูฟังแบบตัดเสียงรบกวน", "ชิ้น", 50, 1890.00),
]


def display_width(text: str) -> int:
    width = 0
    for character in str(text):
        if unicodedata.category(character) in ("Mn", "Me", "Cf"):
            continue
        width += 2 if unicodedata.east_asian_width(character) in ("W", "F") else 1
    return width


def pad(text: object, width: int, align_right: bool = False) -> str:
    value = str(text)
    spaces = " " * (width - display_width(value))
    return spaces + value if align_right else value + spaces


def build_report() -> str:
    widths = [8, 14, 38, 8, 10, 14]
    headers = ["ItemID", "Category", "Name", "Unit", "Quantity", "Unit Price"]
    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"

    def row(values: list[object]) -> str:
        cells = []
        for index, (value, width) in enumerate(zip(values, widths)):
            cells.append(" " + pad(value, width, index in (0, 4, 5)) + " ")
        return "|" + "|".join(cells) + "|"

    lines = [
        "ITEM DATA PREVIEW - 40 RECORDS",
        "ข้อมูลตัวอย่างแยกจากโปรแกรมหลัก",
        "",
        border,
        row(headers),
        border,
    ]

    total_value = 0.0
    for item_id, category, name, unit, quantity, price in ITEMS:
        lines.append(row([item_id, category, name, unit, quantity, f"{price:,.2f}"]))
        total_value += quantity * price

    lines.extend(
        [
            border,
            "",
            f"Total Records : {len(ITEMS)}",
            f"Total Quantity: {sum(item[4] for item in ITEMS):,}",
            f"Total Value   : {total_value:,.2f} THB",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT_FILE.write_text(build_report(), encoding="utf-8", newline="\n")
    print(f"สร้างไฟล์แล้ว: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
