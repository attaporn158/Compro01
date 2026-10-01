import struct
import os
import math
import time
import unicodedata
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent

ITEM_FILE = BASE_DIR / "items.dat"
CATEGORY_FILE = BASE_DIR / "categories.dat"
SALE_FILE = BASE_DIR / "sales.dat"
TOP10_REPORT_FILE = BASE_DIR / "top10_sales_report.txt"
LAST30_REPORT_FILE = BASE_DIR / "sales_last_30_days_report.txt"
TODAY_REPORT_FILE = BASE_DIR / "sales_today_report.txt"

ITEM_STRUCT = struct.Struct("<II128s48s48sIIfB3x")
CATEGORY_STRUCT = struct.Struct("<I128s256sB3x")
SALE_STRUCT = struct.Struct("<QIIIf64s")

INITIAL_CATEGORY_NAMES = {
    1: "เครื่องเขียน",
    2: "ของทั่วไป",
    3: "อุปกรณ์",
}
CATEGORY_IDS = {
    name: category_id
    for category_id, name in INITIAL_CATEGORY_NAMES.items()
}

# item_id, category, name, unit, location, quantity, reorder_level, unit_price
INITIAL_ITEM_DATA = [
    (1001, "เครื่องเขียน", "ปากกาลูกลื่นสีน้ำเงิน", "ด้าม", "ชั้น A1", 50, 10, 12.00),
    (1002, "เครื่องเขียน", "ปากกาลูกลื่นสีดำ", "ด้าม", "ชั้น A1", 50, 10, 12.00),
    (1003, "เครื่องเขียน", "ดินสอ 2B", "แท่ง", "ชั้น A1", 50, 10, 8.00),
    (1004, "เครื่องเขียน", "ยางลบ", "ก้อน", "ชั้น A1", 50, 10, 10.00),
    (1005, "เครื่องเขียน", "กบเหลาดินสอ", "อัน", "ชั้น A1", 50, 10, 15.00),
    (1006, "เครื่องเขียน", "ปากกาเน้นข้อความ", "ด้าม", "ชั้น A2", 50, 10, 25.00),
    (1007, "เครื่องเขียน", "ไม้บรรทัด 30 ซม.", "อัน", "ชั้น A2", 50, 10, 18.00),
    (1008, "เครื่องเขียน", "สมุดโน้ต A5", "เล่ม", "ชั้น A2", 50, 10, 35.00),
    (1009, "เครื่องเขียน", "กระดาษถ่ายเอกสาร A4", "รีม", "ชั้น A2", 50, 10, 125.00),
    (1010, "เครื่องเขียน", "ลิควิดเทป", "อัน", "ชั้น A2", 50, 10, 30.00),
    (1011, "ของทั่วไป", "กระดาษทิชชู", "ห่อ", "ชั้น B1", 50, 10, 25.00),
    (1012, "ของทั่วไป", "กล่องใส่เอกสาร", "กล่อง", "ชั้น B1", 50, 10, 65.00),
    (1013, "ของทั่วไป", "แฟ้มใส A4", "เล่ม", "ชั้น B1", 50, 10, 20.00),
    (1014, "ของทั่วไป", "คลิปหนีบกระดาษ", "กล่อง", "ชั้น B1", 50, 10, 35.00),
    (1015, "ของทั่วไป", "เทปใส", "ม้วน", "ชั้น B1", 50, 10, 22.00),
    (1016, "ของทั่วไป", "กรรไกร", "อัน", "ชั้น B2", 50, 10, 45.00),
    (1017, "ของทั่วไป", "คัตเตอร์", "อัน", "ชั้น B2", 50, 10, 30.00),
    (1018, "ของทั่วไป", "กระดาษโน้ตกาว", "แพ็ก", "ชั้น B2", 50, 10, 40.00),
    (1019, "ของทั่วไป", "ถ่าน AA", "แพ็ก", "ชั้น B2", 50, 10, 85.00),
    (1020, "ของทั่วไป", "ถ่าน AAA", "แพ็ก", "ชั้น B2", 50, 10, 85.00),
    (1021, "อุปกรณ์", "สาย USB-A to USB-C 1 เมตร", "เส้น", "ชั้น C1", 50, 10, 99.00),
    (1022, "อุปกรณ์", "สาย USB-A to USB-C 2 เมตร", "เส้น", "ชั้น C1", 50, 10, 149.00),
    (1023, "อุปกรณ์", "สาย USB-C to USB-C 1 เมตร", "เส้น", "ชั้น C1", 50, 10, 179.00),
    (1024, "อุปกรณ์", "สาย USB-C to USB-C 2 เมตร", "เส้น", "ชั้น C1", 50, 10, 249.00),
    (1025, "อุปกรณ์", "สาย USB-A to Lightning 1 เมตร", "เส้น", "ชั้น C1", 50, 10, 199.00),
    (1026, "อุปกรณ์", "สาย USB-C to Lightning 1 เมตร", "เส้น", "ชั้น C2", 50, 10, 299.00),
    (1027, "อุปกรณ์", "สาย Micro-USB 1 เมตร", "เส้น", "ชั้น C2", 50, 10, 79.00),
    (1028, "อุปกรณ์", "สายชาร์จแม่เหล็ก USB-C", "เส้น", "ชั้น C2", 50, 10, 189.00),
    (1029, "อุปกรณ์", "สายชาร์จนาฬิกาอัจฉริยะ", "เส้น", "ชั้น C2", 50, 10, 259.00),
    (1030, "อุปกรณ์", "สายชาร์จ 3 หัว", "เส้น", "ชั้น C2", 50, 10, 159.00),
    (1031, "อุปกรณ์", "หูฟังมีสายหัว 3.5 มม.", "ชิ้น", "ชั้น C3", 50, 10, 199.00),
    (1032, "อุปกรณ์", "หูฟังมีสายหัว USB-C", "ชิ้น", "ชั้น C3", 50, 10, 299.00),
    (1033, "อุปกรณ์", "หูฟังมีสายหัว Lightning", "ชิ้น", "ชั้น C3", 50, 10, 399.00),
    (1034, "อุปกรณ์", "หูฟังไร้สายแบบอินเอียร์", "คู่", "ชั้น C3", 50, 10, 690.00),
    (1035, "อุปกรณ์", "หูฟังไร้สายแบบครอบหู", "ชิ้น", "ชั้น C3", 50, 10, 1290.00),
    (1036, "อุปกรณ์", "หูฟังแบบเอียร์บัด", "คู่", "ชั้น C4", 50, 10, 590.00),
    (1037, "อุปกรณ์", "หูฟังเกมมิงมีไมโครโฟน", "ชิ้น", "ชั้น C4", 50, 10, 990.00),
    (1038, "อุปกรณ์", "หูฟังครอบหูแบบมีสาย", "ชิ้น", "ชั้น C4", 50, 10, 750.00),
    (1039, "อุปกรณ์", "หูฟังบลูทูธแบบคล้องคอ", "ชิ้น", "ชั้น C4", 50, 10, 850.00),
    (1040, "อุปกรณ์", "หูฟังแบบตัดเสียงรบกวน", "ชิ้น", "ชั้น C4", 50, 10, 1890.00),
]

def encode_fixed(text: str, size: int, field_name: str) ->bytes:
    text = text.strip()
    if "\x00" in text:
        raise ValueError(f"{field_name} มีอักขระที่ใช้ไม่ได้")
    
    data = text.encode("utf-8")
    if len(data) > size:
        raise ValueError(
            f"{field_name} ยาว {len(data)} ไบต์ "
            f"แต่ช่องนี้รับได้ไม่เกิน {size} ไบต์"
        )
        
    return data.ljust(size, b"\x00")

def decode_fixed(data: bytes) -> str:
    return data.split(b"\x00", 1)[0].decode("utf-8")


def create_initial_item_file() -> bool:
    """สร้าง items.dat จำนวน 40 ระเบียนครั้งแรก โดยไม่เขียนทับไฟล์เดิม."""
    if ITEM_FILE.exists():
        return False

    packed_records = []
    for item in INITIAL_ITEM_DATA:
        item_id, category, name, unit, location, quantity, reorder, price = item
        record = (
            item_id,
            CATEGORY_IDS[category],
            encode_fixed(name, 128, "ชื่อพัสดุ"),
            encode_fixed(unit, 48, "หน่วยนับ"),
            encode_fixed(location, 48, "ตำแหน่งจัดเก็บ"),
            quantity,
            reorder,
            price,
            1,
        )
        packed_records.append(ITEM_STRUCT.pack(*record))

    with ITEM_FILE.open("xb") as file:
        file.write(b"".join(packed_records))
        file.flush()
        os.fsync(file.fileno())

    return True

def character_width(char: str) -> int:
    if unicodedata.category(char) in ("Mn", "Me", "Cf"):
        return 0
    if unicodedata.east_asian_width(char) in ("W", "F"):
        return 2
    return 1

def display_width(text: str) -> int:
    return sum(character_width(char) for char in text)

def wrap_display(text: str, width: int) -> list[str]:
    if width < 1:
        raise ValueError("ความกว้างต้องมากกว่า 0")
    
    lines = []
    current = ""
    current_width = 0
    
    for char in text:
        char_width = character_width(char)
        if current and current_width + char_width > width:
            lines.append(current)
            current = ""
            current_width = 0
            
        current += char
        current_width += char_width
        
    lines.append(current)
    return lines

def table_border(widths: list[int]) -> str:
    return "+" + "+".join("-" * (width + 2) for width in widths) + "+"


def table_row(values: list[str], widths: list[int]) -> list[str]:
    if not widths or len(values) != len(widths):
        raise ValueError("จำนวนข้อมูลกับคอลัมน์ไม่ตรงกัน")
    
    wrapped = [
        wrap_display(str(value), width)
        for value, width in zip(values, widths)
    ]
    height = max(len(parts) for parts in wrapped)
    rows = []
    
    for line_number in range(height):
        cells = []
        for parts, width in zip(wrapped, widths):
            piece = parts[line_number] if line_number < len(parts) else ""
            spaces = width - display_width(piece)
            cells.append(" " + piece + (" " * spaces) + " ")
        rows.append("|" + "|".join(cells) + "|")

    return rows

def build_item_table(items: list[tuple]) -> list[str]:
    widths = [10, 10, 24, 12, 10, 14, 12]
    border = table_border(widths)
    lines = [border]
    
    headers = [
        "ItemID", "Category", "Name", "Unit",
        "Quantity", "Unit Price", "Stock Status",
    ]
    lines.extend(table_row(headers, widths))
    lines.append(border)
    
    for item in items:
        if item[5] == 0:
            stock_status = "Out of Stock"
        elif item[5] <= item[6]:
            stock_status = "Low Stock"
        else:
            stock_status = "In Stock"

        values = [
            str(item[0]),
            INITIAL_CATEGORY_NAMES.get(item[1], f"ไม่ทราบ ({item[1]})"),
            decode_fixed(item[2]),
            decode_fixed(item[3]),
            str(item[5]),
            f"{item[7]:,.2f}",
            stock_status,
        ]
        lines.extend(table_row(values, widths))
        lines.append(border)
        
    return lines


def read_records(path: Path, record_struct: struct.Struct) -> list[tuple]:
    if not path.exists():
        return []
    
    data = path.read_bytes()
    
    if len(data) % record_struct.size != 0:
        raise ValueError(f'ไฟล์ {path.name} มีระเบียนขนาดไม่ครบ')
    
    return list(record_struct.iter_unpack(data))

def append_record(
    path: Path, record_struct: struct.Struct, values: tuple) -> None:
    data = record_struct.pack(*values)
    
    with path.open("ab") as file:
        file.write(data)
        file.flush()
        os.fsync(file.fileno())

def write_record_at(
    path: Path, record_struct: struct.Struct, index: int, values: tuple) -> None:
    if index < 0:
        raise IndexError('ตำแหน่งระเบียนไม่ถูกต้อง')
    
    data = record_struct.pack(*values)
    
    with path.open("r+b") as file:
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        
        if file_size % record_struct.size != 0:
            raise ValueError(f"ไฟล์ {path.name} มีระเบียนขนาดไม่ครบ")

        offset = index * record_struct.size
        if offset >= file_size:
            raise IndexError("ไม่พบระเบียนในตำแหน่งนี้")

        file.seek(offset)
        file.write(data)
        file.flush()
        os.fsync(file.fileno())

def find_active_item(item_id: int) -> tuple[int, tuple] | None:
    items = read_records(ITEM_FILE, ITEM_STRUCT)

    for index, record in enumerate(items):
        if record[0] == item_id and record[8] == 1:
            return index, record

    return None

def input_uint32(label: str, minimum: int = 0) -> int:
    raw = input(label).strip()
    if not raw.isascii() or not raw.isdecimal():
        raise ValueError(f"{label}ต้องเป็นจำนวนเต็ม")
    value = int(raw)
    if not minimum <= value <= 0xFFFFFFFF:
        raise ValueError(f"{label}ต้องอยู่ระหว่าง {minimum} ถึง 4294967295")
    return value

def create_initial_category_file() -> bool:
    """สร้างหมวดหมู่เริ่มต้น 3 รายการ โดยไม่เขียนทับไฟล์เดิม."""
    if CATEGORY_FILE.exists():
        return False

    descriptions = {
        1: "สินค้าเครื่องเขียนและอุปกรณ์สำนักงาน",
        2: "ของใช้ทั่วไปภายในร้าน",
        3: "สายชาร์จ หูฟัง และอุปกรณ์อิเล็กทรอนิกส์",
    }
    records = []
    for category_id, name in INITIAL_CATEGORY_NAMES.items():
        records.append(
            CATEGORY_STRUCT.pack(
                category_id,
                encode_fixed(name, 128, "ชื่อหมวดหมู่"),
                encode_fixed(descriptions[category_id], 256, "รายละเอียดหมวดหมู่"),
                1,
            )
        )

    with CATEGORY_FILE.open("xb") as file:
        file.write(b"".join(records))
        file.flush()
        os.fsync(file.fileno())
    return True


def initialize_sales_system() -> None:
    create_initial_item_file()
    create_initial_category_file()
    if not SALE_FILE.exists():
        with SALE_FILE.open("xb") as file:
            file.flush()
            os.fsync(file.fileno())


def restock_item() -> None:
    try:
        item_id = input_uint32("รหัสสินค้าที่เติมสต็อก: ", minimum=1)
        found = find_active_item(item_id)
        if found is None:
            raise ValueError("ไม่พบสินค้าที่ใช้งานอยู่")

        index, old_record = found
        print(f"สินค้า: {decode_fixed(old_record[2])}")
        print(f"คงเหลือเดิม: {old_record[5]} {decode_fixed(old_record[3])}")

        quantity = input_uint32("จำนวนที่รับเข้า: ", minimum=1)
        new_quantity = old_record[5] + quantity
        if new_quantity > 0xFFFFFFFF:
            raise ValueError("จำนวนคงเหลือเกินขนาดที่จัดเก็บได้")

        updated = list(old_record)
        updated[5] = new_quantity
        updated = tuple(updated)
        ITEM_STRUCT.pack(*updated)
    except (ValueError, OverflowError, struct.error) as error:
        print(f"ข้อมูลไม่ถูกต้อง: {error}")
        return

    write_record_at(ITEM_FILE, ITEM_STRUCT, index, updated)
    print(f"เติมสต็อกแล้ว คงเหลือ {new_quantity} {decode_fixed(updated[3])}")


def add_new_item() -> None:
    try:
        item_id = input_uint32("รหัสสินค้าใหม่: ", minimum=1)
        items = read_records(ITEM_FILE, ITEM_STRUCT)
        if any(item[0] == item_id for item in items):
            raise ValueError("รหัสสินค้านี้มีอยู่แล้ว")

        print("\nเลือกหมวดหมู่:")
        for category_id, category_name in INITIAL_CATEGORY_NAMES.items():
            print(f"  [{category_id}] {category_name}")
        print("  [0] ย้อนกลับไปหน้าหลัก")

        category_id = input_uint32("เลือกหมวดหมู่ [0-3]: ")
        if category_id == 0:
            print("ยกเลิกการเพิ่มสินค้า และย้อนกลับไปหน้าหลัก")
            return
        if category_id not in INITIAL_CATEGORY_NAMES:
            raise ValueError("กรุณาเลือกหมวดหมู่ 1, 2 หรือ 3")

        name = input("ชื่อสินค้า: ").strip()
        unit = input("หน่วยนับ: ").strip()
        location = input("ตำแหน่งจัดเก็บ: ").strip()
        if not all((name, unit, location)):
            raise ValueError("ชื่อสินค้า หน่วยนับ และตำแหน่งจัดเก็บห้ามว่าง")

        quantity = input_uint32("จำนวนเริ่มต้น: ")
        reorder_level = input_uint32("จุดสั่งซื้อขั้นต่ำ: ")
        price_text = input("ราคาต่อหน่วย: ").strip()
        unit_price = float(price_text)
        if not math.isfinite(unit_price) or unit_price < 0:
            raise ValueError("ราคาต่อหน่วยต้องเป็นตัวเลขตั้งแต่ 0 ขึ้นไป")

        record = (
            item_id,
            category_id,
            encode_fixed(name, 128, "ชื่อสินค้า"),
            encode_fixed(unit, 48, "หน่วยนับ"),
            encode_fixed(location, 48, "ตำแหน่งจัดเก็บ"),
            quantity,
            reorder_level,
            unit_price,
            1,
        )
        ITEM_STRUCT.pack(*record)
    except (ValueError, OverflowError, struct.error) as error:
        print(f"ข้อมูลไม่ถูกต้อง: {error}")
        return

    append_record(ITEM_FILE, ITEM_STRUCT, record)
    print(f"เพิ่มสินค้า {item_id}: {name} แล้ว")


def sell_item() -> None:
    try:
        item_id = input_uint32("รหัสสินค้าที่ขาย: ", minimum=1)
        found = find_active_item(item_id)
        if found is None:
            raise ValueError("ไม่พบสินค้าที่ใช้งานอยู่")

        index, old_record = found
        print(f"สินค้า: {decode_fixed(old_record[2])}")
        print(f"คงเหลือ: {old_record[5]} {decode_fixed(old_record[3])}")
        print(f"ราคาต่อหน่วย: {old_record[7]:,.2f} บาท")

        quantity = input_uint32("จำนวนที่ขาย: ", minimum=1)
        if quantity > old_record[5]:
            raise ValueError("สินค้าในคลังมีไม่เพียงพอ")

        seller = input("ชื่อผู้ขาย: ").strip()
        if not seller:
            raise ValueError("ชื่อผู้ขายห้ามว่าง")

        sales = read_records(SALE_FILE, SALE_STRUCT)
        sale_id = max((sale[1] for sale in sales), default=0) + 1
        if sale_id > 0xFFFFFFFF:
            raise ValueError("เลขที่การขายเต็มแล้ว")

        updated = list(old_record)
        updated[5] = old_record[5] - quantity
        updated = tuple(updated)
        sale_record = (
            int(time.time()),
            sale_id,
            item_id,
            quantity,
            old_record[7],
            encode_fixed(seller, 64, "ชื่อผู้ขาย"),
        )

        ITEM_STRUCT.pack(*updated)
        SALE_STRUCT.pack(*sale_record)
    except (ValueError, OverflowError, struct.error) as error:
        print(f"ข้อมูลไม่ถูกต้อง: {error}")
        return

    write_record_at(ITEM_FILE, ITEM_STRUCT, index, updated)
    append_record(SALE_FILE, SALE_STRUCT, sale_record)
    total = quantity * old_record[7]
    print(f"บันทึกการขายเลขที่ {sale_id} แล้ว")
    print(f"ยอดขาย {total:,.2f} บาท | คงเหลือ {updated[5]}")


def item_name_map() -> dict[int, str]:
    return {
        item[0]: decode_fixed(item[2])
        for item in read_records(ITEM_FILE, ITEM_STRUCT)
    }


def build_top10_sales_table(sales: list[tuple]) -> list[str]:
    widths = [6, 10, 38, 14, 18]
    border = table_border(widths)
    lines = [border]
    lines.extend(table_row(["Rank", "ItemID", "Name", "Qty Sold", "Revenue"], widths))
    lines.append(border)

    totals: dict[int, list[float]] = {}
    for sale in sales:
        item_id = sale[2]
        if item_id not in totals:
            totals[item_id] = [0, 0.0]
        totals[item_id][0] += sale[3]
        totals[item_id][1] += sale[3] * sale[4]

    names = item_name_map()
    ranking = sorted(
        totals.items(),
        key=lambda entry: (-entry[1][0], -entry[1][1], entry[0]),
    )[:10]

    if not ranking:
        lines.extend(table_row(["-", "-", "ยังไม่มีข้อมูลการขาย", "0", "0.00"], widths))
        lines.append(border)
        return lines

    for rank, (item_id, values) in enumerate(ranking, start=1):
        lines.extend(
            table_row(
                [rank, item_id, names.get(item_id, "ไม่พบชื่อสินค้า"), int(values[0]), f"{values[1]:,.2f}"],
                widths,
            )
        )
        lines.append(border)
    return lines


def build_sales_detail_table(sales: list[tuple]) -> list[str]:
    widths = [19, 8, 10, 34, 10, 14, 16, 20]
    border = table_border(widths)
    lines = [border]
    headers = ["Date/Time", "SaleID", "ItemID", "Name", "Quantity", "Unit Price", "Total", "Seller"]
    lines.extend(table_row(headers, widths))
    lines.append(border)
    names = item_name_map()

    if not sales:
        lines.extend(table_row(["-", "-", "-", "ยังไม่มีข้อมูลการขาย", "0", "0.00", "0.00", "-"], widths))
        lines.append(border)
        return lines

    for sale in sorted(sales, key=lambda record: (record[0], record[1]), reverse=True):
        sold_at = datetime.fromtimestamp(sale[0]).astimezone()
        total = sale[3] * sale[4]
        lines.extend(
            table_row(
                [
                    sold_at.strftime("%Y/%m/%d %H:%M:%S"),
                    sale[1],
                    sale[2],
                    names.get(sale[2], "ไม่พบชื่อสินค้า"),
                    sale[3],
                    f"{sale[4]:,.2f}",
                    f"{total:,.2f}",
                    decode_fixed(sale[5]),
                ],
                widths,
            )
        )
        lines.append(border)
    return lines


def write_sales_report(path: Path, title: str, table_lines: list[str], sales: list[tuple]) -> None:
    line_width = max(display_width(line) for line in table_lines)
    separator = "=" * line_width
    total_quantity = sum(sale[3] for sale in sales)
    total_revenue = sum(sale[3] * sale[4] for sale in sales)
    lines = [
        separator,
        title.center(line_width),
        separator,
        f" Generated At   : {datetime.now().astimezone():%Y/%m/%d %H:%M:%S}",
        f" Sale Records  : {len(sales):,}",
        f" Quantity Sold : {total_quantity:,}",
        f" Total Revenue : {total_revenue:,.2f} THB",
        separator,
        "",
    ]
    lines.extend(table_lines)

    footer = "END OF REPORT - สิ้นสุดรายงาน"
    remaining = line_width - display_width(footer)
    left = remaining // 2
    right = remaining - left
    lines.extend(
        [
            "",
            separator,
            (" " * left) + footer + (" " * right),
            separator,
        ]
    )

    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines) + "\n")
        file.flush()
        os.fsync(file.fileno())
    print(f"สร้างรายงานแล้ว: {path}")


def generate_top10_sales_report() -> None:
    sales = read_records(SALE_FILE, SALE_STRUCT)
    write_sales_report(
        TOP10_REPORT_FILE,
        "TOP 10 BEST-SELLING ITEMS REPORT",
        build_top10_sales_table(sales),
        sales,
    )


def generate_last_30_days_report() -> None:
    now = datetime.now().astimezone()
    start = now - timedelta(days=30)
    sales = [
        sale for sale in read_records(SALE_FILE, SALE_STRUCT)
        if datetime.fromtimestamp(sale[0]).astimezone() >= start
    ]
    write_sales_report(
        LAST30_REPORT_FILE,
        "SALES DURING THE LAST 30 DAYS",
        build_sales_detail_table(sales),
        sales,
    )


def generate_today_sales_report() -> None:
    today = datetime.now().astimezone().date()
    sales = [
        sale for sale in read_records(SALE_FILE, SALE_STRUCT)
        if datetime.fromtimestamp(sale[0]).astimezone().date() == today
    ]
    write_sales_report(
        TODAY_REPORT_FILE,
        "TODAY SALES REPORT",
        build_sales_detail_table(sales),
        sales,
    )


def build_main_menu() -> list[str]:
    menu_width = 64

    def centered(text: str) -> str:
        remaining = menu_width - display_width(text)
        left = remaining // 2
        return (" " * left) + text

    return [
        "=" * menu_width,
        centered("ระบบขายสินค้าในคลัง"),
        "=" * menu_width,
        "",
        "  จัดการสินค้า",
        "  -------------",
        "    [1] ขายสินค้า",
        "    [2] เติมสต็อกสินค้าเดิม",
        "    [3] เพิ่มสินค้าชนิดใหม่",
        "    [4] ดูสินค้าคงเหลือ",
        "",
        "  รายงานการขาย",
        "  --------------",
        "    [5] Top 10 สินค้าขายดี",
        "    [6] การขายย้อนหลัง 30 วัน",
        "    [7] การขายวันนี้",
        "",
        "-" * menu_width,
        "    [0] ออกจากโปรแกรม",
        "-" * menu_width,
    ]


def select_action(title: str, action_text: str) -> bool:
    while True:
        print("\n" + ("-" * 48))
        print(f"  {title}")
        print("-" * 48)
        print(f"  [1] {action_text}")
        print("  [0] ย้อนกลับไปหน้าหลัก")
        print("-" * 48)

        choice = input("เลือกเมนู [0-1]: ").strip()
        if choice == "1":
            return True
        if choice == "0":
            print("ย้อนกลับไปหน้าหลัก")
            return False
        print("กรุณาเลือก 0 หรือ 1")


def main():
    initialize_sales_system()
    while True:
        print("\n" + "\n".join(build_main_menu()))

        choice = input("เลือกเมนู [0-7]: ").strip()

        if choice == "0":
            print("ปิดโปรแกรม")
            break
        elif choice == "1":
            if select_action("เมนูขายสินค้า", "เริ่มบันทึกการขาย"):
                sell_item()
        elif choice == "2":
            if select_action("เมนูเติมสต็อก", "เพิ่มจำนวนสินค้า"):
                restock_item()
        elif choice == "3":
            if select_action("เมนูเพิ่มสินค้าใหม่", "เพิ่มข้อมูลสินค้า"):
                add_new_item()
        elif choice == "4":
            print("\n".join(build_item_table(read_records(ITEM_FILE, ITEM_STRUCT))))
        elif choice == "5":
            generate_top10_sales_report()
        elif choice == "6":
            generate_last_30_days_report()
        elif choice == "7":
            generate_today_sales_report()
        else:
            print("กรุณาเลือกหมายเลขเมนูที่แสดง")


if __name__ == "__main__":
    main()
