import struct
import os
import math
import time
import unicodedata
from difflib import get_close_matches
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
REPORT_TIMEZONE = ZoneInfo("Asia/Bangkok")

ITEM_FILE = BASE_DIR / "items.dat"
CATEGORY_FILE = BASE_DIR / "categories.dat"
SALE_FILE = BASE_DIR / "sales.dat"
TOP10_REPORT_FILE = BASE_DIR / "top10_sales_report.txt"
LAST30_REPORT_FILE = BASE_DIR / "sales_last_30_days_report.txt"
CATEGORY_SALES_REPORT_FILE = BASE_DIR / "sales_by_category_report.txt"

ITEM_STRUCT = struct.Struct("<II128s48s48sIIfB3x")
CATEGORY_STRUCT = struct.Struct("<I128s256sB3x")
SALE_STRUCT = struct.Struct("<QIIIf64s128s128sI")

INITIAL_CATEGORY_NAMES = {1: 'เครื่องเขียน', 2: 'ของทั่วไป', 3: 'สายชาร์จ', 4: 'หูฟัง', 5: 'อุปกรณ์เสริม'}
CATEGORY_IDS = {name: category_id for category_id, name in INITIAL_CATEGORY_NAMES.items()}

# item_id, category, name, unit, location, quantity, reorder_level, unit_price
INITIAL_ITEM_DATA = [
    (1, 'เครื่องเขียน', 'ปากกาลูกลื่นสีน้ำเงิน', 'ด้าม', 'ชั้น A1', 30, 10, 12.0),
    (2, 'เครื่องเขียน', 'ปากกาลูกลื่นสีดำ', 'ด้าม', 'ชั้น A1', 30, 10, 12.0),
    (3, 'เครื่องเขียน', 'ดินสอ 2B', 'แท่ง', 'ชั้น A1', 30, 10, 8.0),
    (4, 'เครื่องเขียน', 'ยางลบ', 'ก้อน', 'ชั้น A1', 30, 10, 10.0),
    (5, 'เครื่องเขียน', 'กบเหลาดินสอ', 'อัน', 'ชั้น A1', 30, 10, 15.0),
    (6, 'เครื่องเขียน', 'ปากกาเน้นข้อความ', 'ด้าม', 'ชั้น A1', 30, 10, 25.0),
    (7, 'ของทั่วไป', 'กระดาษทิชชู', 'ห่อ', 'ชั้น B1', 30, 10, 25.0),
    (8, 'ของทั่วไป', 'กล่องใส่เอกสาร', 'กล่อง', 'ชั้น B1', 30, 10, 65.0),
    (9, 'ของทั่วไป', 'เทปใส', 'ม้วน', 'ชั้น B1', 30, 10, 22.0),
    (10, 'ของทั่วไป', 'กรรไกร', 'อัน', 'ชั้น B1', 30, 10, 45.0),
    (11, 'ของทั่วไป', 'ถ่าน AA', 'แพ็ก', 'ชั้น B1', 30, 10, 85.0),
    (12, 'ของทั่วไป', 'ถ่าน AAA', 'แพ็ก', 'ชั้น B1', 30, 10, 85.0),
    (13, 'สายชาร์จ', 'สาย USB-A to USB-C 1 เมตร', 'เส้น', 'ชั้น C1', 30, 10, 99.0),
    (14, 'สายชาร์จ', 'สาย USB-A to USB-C 2 เมตร', 'เส้น', 'ชั้น C1', 30, 10, 149.0),
    (15, 'สายชาร์จ', 'สาย USB-C to USB-C 1 เมตร', 'เส้น', 'ชั้น C1', 30, 10, 179.0),
    (16, 'สายชาร์จ', 'สาย USB-C to USB-C 2 เมตร', 'เส้น', 'ชั้น C1', 30, 10, 249.0),
    (17, 'สายชาร์จ', 'สาย USB-A to Lightning 1 เมตร', 'เส้น', 'ชั้น C1', 30, 10, 199.0),
    (18, 'สายชาร์จ', 'สาย USB-C to Lightning 1 เมตร', 'เส้น', 'ชั้น C1', 30, 10, 299.0),
    (19, 'หูฟัง', 'หูฟังมีสายหัว 3.5 มม.', 'ชิ้น', 'ชั้น D1', 30, 10, 199.0),
    (20, 'หูฟัง', 'หูฟังมีสายหัว USB-C', 'ชิ้น', 'ชั้น D1', 30, 10, 299.0),
    (21, 'หูฟัง', 'หูฟังมีสายหัว Lightning', 'ชิ้น', 'ชั้น D1', 30, 10, 399.0),
    (22, 'หูฟัง', 'หูฟังไร้สายแบบอินเอียร์', 'คู่', 'ชั้น D1', 30, 10, 690.0),
    (23, 'หูฟัง', 'หูฟังไร้สายแบบครอบหู', 'ชิ้น', 'ชั้น D1', 30, 10, 1290.0),
    (24, 'หูฟัง', 'หูฟังแบบเอียร์บัด', 'คู่', 'ชั้น D1', 30, 10, 590.0),
    (25, 'อุปกรณ์เสริม', 'หัวชาร์จ USB-A', 'ชิ้น', 'ชั้น E1', 30, 10, 149.0),
    (26, 'อุปกรณ์เสริม', 'หัวชาร์จ USB-C 20W', 'ชิ้น', 'ชั้น E1', 30, 10, 299.0),
    (27, 'อุปกรณ์เสริม', 'พาวเวอร์แบงก์ 10000 mAh', 'ชิ้น', 'ชั้น E1', 30, 10, 590.0),
    (28, 'อุปกรณ์เสริม', 'ขาตั้งโทรศัพท์', 'ชิ้น', 'ชั้น E1', 30, 10, 89.0),
    (29, 'อุปกรณ์เสริม', 'เมาส์ไร้สาย', 'ชิ้น', 'ชั้น E1', 30, 10, 199.0),
    (30, 'อุปกรณ์เสริม', 'แผ่นรองเมาส์', 'ชิ้น', 'ชั้น E1', 30, 10, 59.0),
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


def create_initial_item_file() -> None:
    """สร้าง items.dat จำนวน 30 ระเบียนครั้งแรก โดยไม่เขียนทับไฟล์เดิม."""
    if ITEM_FILE.exists():
        return

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
    categories = {
        category[0]: decode_fixed(category[1])
        for category in read_records(CATEGORY_FILE, CATEGORY_STRUCT)
    }
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
        if item[8] != 1:
            continue
        if item[5] == 0:
            stock_status = "Out of Stock"
        elif item[5] <= item[6]:
            stock_status = "Low Stock"
        else:
            stock_status = "In Stock"

        values = [
            str(item[0]),
            categories.get(item[1], f"ไม่ทราบ ({item[1]})"),
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

def replace_records(path: Path, record_struct: struct.Struct, records: list[tuple]) -> None:
    data = b"".join(record_struct.pack(*record) for record in records)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as file:
        file.write(data)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary, path)


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

def create_initial_category_file() -> None:
    """สร้างหมวดหมู่เริ่มต้น 5 รายการ โดยไม่เขียนทับไฟล์เดิม."""
    if CATEGORY_FILE.exists():
        return

    descriptions = {
        1: "สินค้าเครื่องเขียนและอุปกรณ์สำนักงาน",
        2: "ของใช้ทั่วไปภายในร้าน",
        3: "สายชาร์จและสายเชื่อมต่ออุปกรณ์",
        4: "หูฟังมีสายและหูฟังไร้สาย",
        5: "อุปกรณ์เสริมสำหรับโทรศัพท์และคอมพิวเตอร์",
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

        categories = read_records(CATEGORY_FILE, CATEGORY_STRUCT)
        print("หมวดหมู่ที่มี: " + ", ".join(decode_fixed(category[1]) for category in categories if category[3] == 1))
        category_name = input("ชื่อหมวดหมู่: ").strip()
        if not category_name:
            raise ValueError("ชื่อหมวดหมู่ห้ามว่าง")
        category_key = unicodedata.normalize("NFC", category_name).casefold()
        existing_category = next((
            category for category in categories
            if category[3] == 1 and unicodedata.normalize("NFC", decode_fixed(category[1])).casefold() == category_key
        ), None)
        if existing_category is None:
            raise ValueError("ไม่พบหมวดหมู่ กรุณาเพิ่มผ่านเมนูเพิ่มหมวดหมู่ก่อน")
        category_id = existing_category[0]
        print(f"ใช้หมวดหมู่: {decode_fixed(existing_category[1])}")

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


def delete_item() -> None:
    try:
        item_id = input_uint32("รหัสสินค้าที่ต้องการลบ: ", minimum=1)
        items = read_records(ITEM_FILE, ITEM_STRUCT)
        found = next(((index, item) for index, item in enumerate(items) if item[0] == item_id), None)
        if found is None:
            raise ValueError("ไม่พบรหัสสินค้านี้")
        _, item = found
        remaining = [row for row in items if row[0] != item_id]
        replace_records(ITEM_FILE, ITEM_STRUCT, remaining)
        print(f"ลบสินค้า {item_id}: {decode_fixed(item[2])} ออกจากไฟล์แล้ว")
    except (OSError, ValueError, OverflowError, struct.error) as error:
        print(f"ลบสินค้าไม่ได้: {error}")


def add_category() -> None:
    try:
        categories = read_records(CATEGORY_FILE, CATEGORY_STRUCT)
        name = input("ชื่อหมวดหมู่ใหม่: ").strip()
        if not name:
            raise ValueError("ชื่อหมวดหมู่ห้ามว่าง")
        key = unicodedata.normalize("NFC", name).casefold()
        keys = {unicodedata.normalize("NFC", decode_fixed(row[1])).casefold(): row for row in categories}
        if key in keys:
            raise ValueError("หมวดหมู่นี้มีอยู่แล้ว")
        similar = get_close_matches(key, list(keys), n=1, cutoff=0.8)
        if similar:
            print(f"มีหมวดหมู่ชื่อใกล้เคียง: {decode_fixed(keys[similar[0]][1])}")
            print("  [1] ใช้หมวดหมู่เดิม ไม่เพิ่มซ้ำ")
            print("  [2] เพิ่มเป็นหมวดหมู่ใหม่")
            while True:
                choice = input("เลือก [1-2]: ").strip()
                if choice == "1":
                    return
                if choice == "2":
                    break
                print("กรุณาเลือก 1 หรือ 2")
        description = input("รายละเอียดหมวดหมู่: ").strip()
        if not description:
            raise ValueError("รายละเอียดหมวดหมู่ห้ามว่าง")
        sales = read_records(SALE_FILE, SALE_STRUCT)
        category_id = max(
            max((row[0] for row in categories), default=0),
            max((sale[8] for sale in sales), default=0),
        ) + 1
        if category_id > 0xFFFFFFFF:
            raise ValueError("รหัสหมวดหมู่เต็มแล้ว")
        record = (category_id, encode_fixed(name, 128, "ชื่อหมวดหมู่"), encode_fixed(description, 256, "รายละเอียดหมวดหมู่"), 1)
        append_record(CATEGORY_FILE, CATEGORY_STRUCT, record)
        print(f"เพิ่มหมวดหมู่ {name} แล้ว")
    except (OSError, ValueError, OverflowError, struct.error) as error:
        print(f"เพิ่มหมวดหมู่ไม่ได้: {error}")


def delete_category() -> None:
    try:
        categories = read_records(CATEGORY_FILE, CATEGORY_STRUCT)
        if not categories:
            print("ไม่มีหมวดหมู่ให้ลบ")
            return
        print("\n".join(build_category_table(categories)))
        category_id = input_uint32("รหัสหมวดหมู่ที่ต้องการลบ: ", minimum=1)
        category = next((row for row in categories if row[0] == category_id), None)
        if category is None:
            raise ValueError("ไม่พบรหัสหมวดหมู่นี้")
        items = read_records(ITEM_FILE, ITEM_STRUCT)
        count = sum(item[1] == category_id for item in items)
        if count:
            raise ValueError(f"หมวดหมู่นี้มีสินค้า {count} รายการ กรุณาลบสินค้าในหมวดหมู่ก่อน")
        replace_records(CATEGORY_FILE, CATEGORY_STRUCT, [row for row in categories if row[0] != category_id])
    except (OSError, ValueError, OverflowError, struct.error) as error:
        print(f"ลบหมวดหมู่ไม่ได้: {error}")


def manage_items_menu() -> None:
    while True:
        print("\n" + "-" * 48)
        print("  จัดการสินค้า")
        print("-" * 48)
        print("  [1] เพิ่มสินค้า")
        print("  [2] ลบสินค้า")
        print("  [3] เพิ่มหมวดหมู่")
        print("  [4] ลบหมวดหมู่")
        print("  [0] ย้อนกลับไปหน้าหลัก")
        print("-" * 48)
        choice = input("เลือกเมนู [0-4]: ").strip()
        if choice == "0":
            return
        if choice == "1":
            add_new_item()
        elif choice == "2":
            delete_item()
        elif choice == "3":
            add_category()
        elif choice == "4":
            delete_category()
        else:
            print("กรุณาเลือก 0, 1, 2, 3 หรือ 4")


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
            old_record[2],
            encode_fixed(item_category_map().get(item_id, "ไม่พบหมวดหมู่"), 128, "ชื่อหมวดหมู่"),
            old_record[1],
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
    names = {
        sale[2]: decode_fixed(sale[6])
        for sale in read_records(SALE_FILE, SALE_STRUCT)
    }
    names.update({
        item[0]: decode_fixed(item[2])
        for item in read_records(ITEM_FILE, ITEM_STRUCT)
    })
    return names


def item_category_map() -> dict[int, str]:
    categories = {
        category[0]: decode_fixed(category[1])
        for category in read_records(CATEGORY_FILE, CATEGORY_STRUCT)
    }
    names = {
        sale[2]: decode_fixed(sale[7])
        for sale in read_records(SALE_FILE, SALE_STRUCT)
    }
    names.update({
        item[0]: categories.get(item[1], "ไม่พบหมวดหมู่")
        for item in read_records(ITEM_FILE, ITEM_STRUCT)
    })
    return names


def aggregate_sales(sales: list[tuple]) -> dict[int, tuple[int, float]]:
    totals: dict[int, tuple[int, float]] = {}
    for sale in sales:
        quantity, revenue = totals.get(sale[2], (0, 0.0))
        totals[sale[2]] = (quantity + sale[3], revenue + sale[3] * sale[4])
    return totals


def rank_sales(sales: list[tuple]) -> list[tuple[int, tuple[int, float]]]:
    return sorted(
        aggregate_sales(sales).items(),
        key=lambda entry: (-entry[1][0], -entry[1][1], entry[0]),
    )


def build_top10_sales_table(sales: list[tuple]) -> list[str]:
    widths = [6, 10, 38, 16, 14, 18]
    border = table_border(widths)
    lines = [border]
    lines.extend(table_row(["Rank", "ItemID", "Name", "Category", "Qty Sold", "Revenue"], widths))
    lines.append(border)

    names = item_name_map()
    categories = item_category_map()
    ranking = rank_sales(sales)[:10]

    if not ranking:
        lines.extend(table_row(["-", "-", "ยังไม่มีข้อมูลการขาย", "-", "0", "0.00"], widths))
        lines.append(border)
        return lines

    for rank, (item_id, values) in enumerate(ranking, start=1):
        lines.extend(
            table_row(
                [rank, item_id, names.get(item_id, "ไม่พบชื่อสินค้า"), categories.get(item_id, "ไม่พบหมวดหมู่"), int(values[0]), f"{values[1]:,.2f}"],
                widths,
            )
        )
        lines.append(border)
    return lines


def build_sales_detail_table(sales: list[tuple]) -> list[str]:
    widths = [19, 6, 6, 26, 12, 8, 10, 12, 14]
    border = table_border(widths)
    lines = [border]
    headers = ["Date/Time", "SaleID", "ItemID", "Name", "Category", "Quantity", "Unit Price", "Total", "Seller"]
    lines.extend(table_row(headers, widths))
    lines.append(border)
    names = item_name_map()
    categories = item_category_map()

    if not sales:
        lines.extend(table_row(["-", "-", "-", "ยังไม่มีข้อมูลการขาย", "-", "0", "0.00", "0.00", "-"], widths))
        lines.append(border)
        return lines

    for sale in sorted(sales, key=lambda record: (record[0], record[1]), reverse=True):
        sold_at = datetime.fromtimestamp(sale[0], REPORT_TIMEZONE)
        total = sale[3] * sale[4]
        lines.extend(
            table_row(
                [
                    sold_at.strftime("%Y/%m/%d %H:%M:%S"),
                    sale[1],
                    sale[2],
                    names.get(sale[2], "ไม่พบชื่อสินค้า"),
                    categories.get(sale[2], "ไม่พบหมวดหมู่"),
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


def aggregate_category_sales(sales: list[tuple]) -> dict[str, tuple[int, float]]:
    totals: dict[str, tuple[int, float]] = {}
    for sale in sales:
        category = decode_fixed(sale[7])
        quantity, revenue = totals.get(category, (0, 0.0))
        totals[category] = (quantity + sale[3], revenue + sale[3] * sale[4])
    return totals


def aggregate_category_stock() -> dict[str, int]:
    categories = item_category_map()
    stock: dict[str, int] = {}
    for item in read_records(ITEM_FILE, ITEM_STRUCT):
        if item[8] == 1:
            category = categories.get(item[0], "ไม่พบหมวดหมู่")
            stock[category] = stock.get(category, 0) + item[5]
    return stock


def build_category_sales_table(
    totals: dict[str, tuple[int, float]], stock: dict[str, int],
) -> list[str]:
    widths = [6, 24, 14, 14, 18]
    border = table_border(widths)
    lines = [border]
    lines.extend(table_row(["No.", "Category", "Stock Qty", "Qty Sold", "Revenue (THB)"], widths))
    lines.append(border)
    names = sorted(set(totals) | set(stock))
    if not names:
        lines.extend(table_row(["-", "ยังไม่มีข้อมูล", "0", "0", "0.00"], widths))
        lines.append(border)
    for number, category in enumerate(names, 1):
        quantity, revenue = totals.get(category, (0, 0.0))
        lines.extend(table_row([number, category, f"{stock.get(category, 0):,}", f"{quantity:,}", f"{revenue:,.2f}"], widths))
        lines.append(border)
    return lines


def write_sales_report(
    path: Path, title: str, table_lines: list[str], sales: list[tuple],
    period: str, top10: bool = False,
    category_totals: dict[str, tuple[int, float]] | None = None,
    category_stock: dict[str, int] | None = None,
) -> None:
    line_width = max(display_width(line) for line in table_lines)
    separator = "=" * line_width
    total_quantity = sum(sale[3] for sale in sales)
    total_revenue = sum(sale[3] * sale[4] for sale in sales)
    if category_totals is None:
        ranking = rank_sales(sales)
        best_seller = "ยังไม่มีข้อมูลการขายในช่วงนี้"
        if ranking:
            best_id, best_values = ranking[0]
            name = item_name_map().get(best_id, "ไม่พบชื่อสินค้า")
            best_seller = f"{name} (รหัส {best_id}) ขาย {best_values[0]:,} หน่วย"

    generated_at = datetime.now(REPORT_TIMEZONE)
    offset = generated_at.strftime("%z")
    offset = offset[:3] + ":" + offset[3:]
    header = [
        f"Generated At  : {generated_at:%Y-%m-%d %H:%M:%S} ({offset})",
        "App Version   : 1.0",
        "Endianness    : Little-Endian",
        "Encoding      : UTF-8 (fixed-length)",
        f"Report Period : {period}",
    ]
    lines = [separator, title.center(line_width), separator, ""]
    for text in header:
        lines.extend(wrap_display(text, line_width))
    lines.extend([separator, ""])
    lines.extend(table_lines)

    def summary_value(label: str, value: str) -> str:
        padding = " " * max(0, 24 - display_width(label))
        return f"  {label}{padding}: {value}"

    summary = ["สรุปผลรายงาน", ""]
    if category_totals is not None:
        summary.extend([
            summary_value("จำนวนหมวดหมู่ที่ขาย", f"{len(category_totals):,} หมวดหมู่"),
            summary_value("จำนวนรายการขาย", f"{len(sales):,} รายการ"),
            summary_value("จำนวนขายรวม", f"{total_quantity:,} หน่วย"),
            summary_value("ยอดขายรวม", f"{total_revenue:,.2f} บาท"),
        ])
        if category_stock is not None:
            summary.append(summary_value("สต็อกคงเหลือปัจจุบัน", f"{sum(category_stock.values()):,} หน่วย"))
        if category_totals:
            best_quantity = max(category_totals, key=lambda name: (category_totals[name][0], category_totals[name][1]))
            best_revenue = max(category_totals, key=lambda name: (category_totals[name][1], category_totals[name][0]))
            summary.extend([
                "",
                "หมวดหมู่ที่ขายได้มากที่สุด",
                f"  {best_quantity}: {category_totals[best_quantity][0]:,} หน่วย",
                "หมวดหมู่ที่มียอดขายสูงที่สุด",
                f"  {best_revenue}: {category_totals[best_revenue][1]:,.2f} บาท",
            ])
    elif top10:
        displayed = ranking[:10]
        shown_quantity = sum(values[0] for _, values in displayed)
        shown_revenue = sum(values[1] for _, values in displayed)
        summary.extend([
            "สินค้าที่แสดงใน Top 10",
            summary_value("จำนวนชนิดสินค้า", f"{len(displayed)} ชนิด จากที่ขายทั้งหมด {len(ranking)} ชนิด"),
            summary_value("จำนวนขาย", f"{shown_quantity:,} หน่วย"),
            summary_value("ยอดขาย", f"{shown_revenue:,.2f} บาท"),
            "",
            "ยอดขายทั้งหมดในช่วงรายงาน",
            summary_value("จำนวนรายการขาย", f"{len(sales):,} รายการ"),
            summary_value("จำนวนขาย", f"{total_quantity:,} หน่วย"),
            summary_value("ยอดขาย", f"{total_revenue:,.2f} บาท"),
        ])
    else:
        average = total_revenue / len(sales) if sales else 0.0
        summary.extend([
            summary_value("จำนวนรายการขาย", f"{len(sales):,} รายการ"),
            summary_value("จำนวนชนิดสินค้า", f"{len(ranking):,} ชนิด"),
            summary_value("จำนวนขาย", f"{total_quantity:,} หน่วย"),
            summary_value("ยอดขายรวม", f"{total_revenue:,.2f} บาท"),
            summary_value("ยอดเฉลี่ยต่อรายการ", f"{average:,.2f} บาท"),
        ])
        sellers: dict[str, tuple[int, float]] = {}
        for sale in sales:
            seller = decode_fixed(sale[5])
            count, revenue = sellers.get(seller, (0, 0.0))
            sellers[seller] = (count + 1, revenue + sale[3] * sale[4])
        if sellers:
            summary.extend(["", "ยอดขายแยกตามผู้ขาย"])
            for seller, (count, revenue) in sorted(sellers.items()):
                summary.append(summary_value(seller, f"{revenue:,.2f} บาท ({count:,} รายการ)"))
    if category_totals is None:
        summary.extend(["", "สินค้าขายดีที่สุด", f"  {best_seller}"])
    lines.extend(["", "-" * line_width])
    for text in summary:
        lines.extend(wrap_display(text, line_width))

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
    print(f"สร้างรายงานแล้ว: {path.name}")


def report_sales() -> list[tuple]:
    active_categories = {
        unicodedata.normalize("NFC", decode_fixed(category[1])).casefold(): decode_fixed(category[1])
        for category in read_records(CATEGORY_FILE, CATEGORY_STRUCT)
        if category[3] == 1
    }
    result = []
    for sale in read_records(SALE_FILE, SALE_STRUCT):
        key = unicodedata.normalize("NFC", decode_fixed(sale[7])).casefold()
        if key in active_categories:
            result.append((*sale[:7], encode_fixed(active_categories[key], 128, "ชื่อหมวดหมู่"), sale[8]))
    return result


def generate_top10_sales_report() -> None:
    sales = report_sales()
    period = "All recorded sales"
    if sales:
        first = datetime.fromtimestamp(min(sale[0] for sale in sales), REPORT_TIMEZONE)
        last = datetime.fromtimestamp(max(sale[0] for sale in sales), REPORT_TIMEZONE)
        period += f" ({first:%Y/%m/%d} - {last:%Y/%m/%d})"
    write_sales_report(
        TOP10_REPORT_FILE,
        "TOP 10 BEST-SELLING ITEMS REPORT",
        build_top10_sales_table(sales),
        sales,
        period,
        top10=True,
    )


def generate_last_30_days_report() -> None:
    now = datetime.now(REPORT_TIMEZONE)
    start = now - timedelta(days=30)
    sales = [
        sale for sale in report_sales()
        if start <= datetime.fromtimestamp(sale[0], REPORT_TIMEZONE) <= now
    ]
    write_sales_report(
        LAST30_REPORT_FILE,
        "SALES DURING THE LAST 30 DAYS",
        build_sales_detail_table(sales),
        sales,
        f"{start:%Y/%m/%d %H:%M:%S} - {now:%Y/%m/%d %H:%M:%S} (last 30 days)",
    )


def generate_category_sales_report() -> None:
    active_categories = {
        category[0]: decode_fixed(category[1])
        for category in read_records(CATEGORY_FILE, CATEGORY_STRUCT)
        if category[3] == 1
    }
    sales = report_sales()
    category_totals = aggregate_category_sales(sales)
    current_stock = aggregate_category_stock()
    category_stock = {name: current_stock.get(name, 0) for name in active_categories.values()}
    period = "All recorded sales"
    if sales:
        first = datetime.fromtimestamp(min(sale[0] for sale in sales), REPORT_TIMEZONE)
        last = datetime.fromtimestamp(max(sale[0] for sale in sales), REPORT_TIMEZONE)
        period += f" ({first:%Y/%m/%d} - {last:%Y/%m/%d})"
    write_sales_report(
        CATEGORY_SALES_REPORT_FILE,
        "SALES BY CATEGORY REPORT",
        build_category_sales_table(category_totals, category_stock),
        sales,
        period,
        category_totals=category_totals,
        category_stock=category_stock,
    )


def build_category_table(categories: list[tuple]) -> list[str]:
    categories = [category for category in categories if category[3] == 1]
    widths = [12, 18, 48, 14]
    border = table_border(widths)
    lines = [border]
    lines.extend(table_row(["CategoryID", "Category", "Description", "Status"], widths))
    lines.append(border)
    if not categories:
        lines.extend(table_row(["-", "ไม่มีข้อมูลหมวดหมู่", "-", "-"], widths))
        lines.append(border)
    for category in categories:
        lines.extend(table_row([
            category[0], decode_fixed(category[1]), decode_fixed(category[2]),
            "ใช้งาน" if category[3] == 1 else "ไม่ใช้งาน",
        ], widths))
        lines.append(border)
    return lines


def build_sale_records_table(sales: list[tuple]) -> list[str]:
    widths = [19, 6, 6, 8, 10, 14]
    border = table_border(widths)
    lines = [border]
    lines.extend(table_row(["Date/Time", "SaleID", "ItemID", "Quantity", "Unit Price", "Seller"], widths))
    lines.append(border)
    if not sales:
        lines.extend(table_row(["-", "-", "-", "0", "0.00", "ไม่มีข้อมูล"], widths))
        lines.append(border)
    for sale in sales:
        lines.extend(table_row([
            datetime.fromtimestamp(sale[0], REPORT_TIMEZONE).strftime("%Y/%m/%d %H:%M:%S"),
            sale[1], sale[2], sale[3], f"{sale[4]:,.2f}", decode_fixed(sale[5]),
        ], widths))
        lines.append(border)
    return lines


def view_data_menu() -> None:
    while True:
        print("\n" + "-" * 64)
        print("  ดูข้อมูลที่จัดเก็บ")
        print("-" * 64)
        print("  [1] ข้อมูลสินค้าและสต็อก")
        print("  [2] ข้อมูลหมวดหมู่สินค้า")
        print("  [3] ดูข้อมูลในไฟล์การขาย")
        print("  [0] ย้อนกลับไปหน้าหลัก")
        print("-" * 64)
        choice = input("เลือกเมนู [0-3]: ").strip()
        if choice == "0":
            return
        try:
            if choice == "1":
                print("\nข้อมูลสินค้าและสต็อก")
                rows = [item for item in read_records(ITEM_FILE, ITEM_STRUCT) if item[8] == 1]
                print("\n".join(build_item_table(rows)))
                print(f"จำนวนสินค้า: {len(rows)} รายการ")
            elif choice == "2":
                print("\nข้อมูลหมวดหมู่สินค้า")
                rows = [category for category in read_records(CATEGORY_FILE, CATEGORY_STRUCT) if category[3] == 1]
                print("\n".join(build_category_table(rows)))
                print(f"จำนวนหมวดหมู่: {len(rows)} รายการ")
            elif choice == "3":
                print("\nข้อมูลที่เก็บใน sales.dat")
                rows = read_records(SALE_FILE, SALE_STRUCT)
                print("\n".join(build_sale_records_table(rows)))
                print(f"จำนวนรายการขาย: {len(rows)} รายการ")
            else:
                print("กรุณาเลือก 0, 1, 2 หรือ 3")
        except (OSError, ValueError) as error:
            print(f"อ่านข้อมูลไม่ได้: {error}")


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
        "    [3] จัดการสินค้า",
        "    [4] ดูข้อมูล",
        "",
        "  รายงานการขาย",
        "  --------------",
        "    [5] Top 10 สินค้าขายดี",
        "    [6] การขายย้อนหลัง 30 วัน",
        "    [7] รายงานยอดขายแยกตามหมวดหมู่",
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
            manage_items_menu()
        elif choice == "4":
            view_data_menu()
        elif choice == "5":
            generate_top10_sales_report()
        elif choice == "6":
            generate_last_30_days_report()
        elif choice == "7":
            generate_category_sales_report()
        else:
            print("กรุณาเลือกหมายเลขเมนูที่แสดง")


if __name__ == "__main__":
    main()
