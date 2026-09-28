import struct
import os
import math
import time
import unicodedata
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent

ITEM_FILE = BASE_DIR / "items.dat"
CATEGORY_FILE = BASE_DIR / "categories.dat"
TRANSACTION_FILE = BASE_DIR / "transactions.dat"
REPORT_FILE = BASE_DIR / "report.txt"

ITEM_STRUCT = struct.Struct("<II128s48s48sIIfB3x")
CATEGORY_STRUCT = struct.Struct("<I128s256sB3x")
TRANSACTION_STRUCT = struct.Struct("<QIBIIf64s128sB3x")

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
    widths = [10, 10, 24, 12, 10, 14, 8]
    border = table_border(widths)
    lines = [border]
    
    headers = [
        "ItemID", "Category", "Name", "Unit",
        "Quantity", "Unit Price", "Status",
    ]
    lines.extend(table_row(headers, widths))
    lines.append(border)
    
    for item in items:
        status = "Active" if item[8] == 1 else "Deleted"
        values = [
           str(item[0]),
            str(item[1]),
            decode_fixed(item[2]),
            decode_fixed(item[3]),
            str(item[5]),
            f"{item[7]:,.2f}",
            status, 
        ]
        lines.extend(table_row(values, widths))
        lines.append(border)
        
    return lines

def build_summary_lines(items: list[tuple]) -> list[str]:
    active = [item for item in items if item[8] == 1]
    deleted = [item for item in items if item[8] == 0]
    
    total_quantity = sum(item[5] for item in active)
    total_value = sum(item[5] * item[7] for item in active)
    low_stock = sum(item[5] <= item[6] for item in active)
    
    return [
        "",
        "Summary",
        f"- Total Items (records): {len(items)}",
        f"- Active Items: {len(active)}",
        f"- Deleted Items: {len(deleted)}",
        f"- Total Quantity: {total_quantity:,}",
        f"- Free Slots: {len(deleted)}",
        f"- Low-Stock Items: {low_stock}",
        f"- Total Inventory Value: {total_value:,.2f} THB",
    ]

def build_statistics_lines(items: list[tuple]) -> list[str]:
    active = [item for item in items if item[8] == 1]
    
    if not active:
        return [
            "",
            "Price Statistics (Active only)",
            "- Min: N/A",
            "- Max: N/A",
            "- Avg: N/A",
            "",
            "Inventory Value Statistics (Active only)",
            "- Total Quantity: 0",
            "- Total Value: 0.00 THB",
            "- Average Value: N/A",
        ]
        
    prices = [item[7] for item in active]
    total_quantity = sum(item[5] for item in active)
    total_value = sum(item[5] * item[7] for item in active)
    
    return [
        "",
        "Price Statistics (Active only)",
        f"- Min: {min(prices):,.2f} THB",
        f"- Max: {max(prices):,.2f} THB",
        f"- Avg: {sum(prices) / len(prices):,.2f} THB",
        "",
        "Inventory Value Statistics (Active only)",
        f"- Total Quantity: {total_quantity:,}",
        f"- Total Value: {total_value:,.2f} THB",
        f"- Average Value: {total_value / len(active):,.2f} THB/item",
    ]

def build_category_lines(items: list[tuple], categories: list[tuple]) -> list[str]:
    names = {
        category[0]: decode_fixed(category[1])
        for category in categories
    }
    counts: dict[int, int] = {}
    
    for item in items:
        if item[8] == 1:
            category_id = item[1]
            counts[category_id] = counts.get(category_id, 0) + 1
            
    lines = ["", "Items by Category (Active only)"]
    if not counts:
        lines.append("- No active items")
        return lines
    
    rows = [
        (f"{names.get(category_id, 'ไม่พบหมวดหมู่')} ({category_id})", count)
        for category_id, count in sorted(counts.items())
    ]
    label_width = max(display_width(label) for label, _ in rows)

    for label, count in rows:
        padding = " " * (label_width - display_width(label))
        lines.append(f"- {label}{padding} : {count}")

    return lines

def build_history_lines(logs: list[tuple], limit: int = 5) -> list[str]:
    operation_names = {
        1: "ADD",
        2: "UPDATE",
        3: "DELETE",
        4: "RECEIVE",
        5: "ISSUE", 
    }
    lines = ["", "Recent Transactions"]
    recent = sorted(logs,key=lambda record: record[1], reverse=True) [:limit]
    
    if not recent:
        lines.append("- No transactions yet")
        return lines
    
    for record in recent:
        when = datetime.fromtimestamp(record[0]).astimezone()
        timestamp = when.strftime("%Y-%m-%d %H:%M:%S %z")
        operation = operation_names.get(record[2], "UNKNOWN")
        status = "Active" if record[8] == 1 else "Deleted"

        lines.append(
            f"- {timestamp} | #{record[1]} {operation} | "
            f"Item {record[3]} | Qty {record[4]} | "
            f"Balance {record[5]:,.2f} | {status}"
        )
        lines.append(f"  Operator: {decode_fixed(record[6])}")

        note = decode_fixed(record[7])
        if note:
            lines.append(f"  Note: {note}")

    return lines

def generate_report() -> None:
    items = read_records(ITEM_FILE, ITEM_STRUCT)
    categories = read_records(CATEGORY_FILE, CATEGORY_STRUCT)
    logs = read_records(TRANSACTION_FILE, TRANSACTION_STRUCT)

    lines = [
        "Inventory Management System - Summary Report",
        f"Generated At : {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "App Version  : 1.0",
        "Endianness   : Little-Endian",
        "Encoding     : UTF-8 (fixed-length binary records)",
        "",
    ]
    
    lines.extend(build_item_table(items))
    lines.extend(build_summary_lines(items))
    lines.extend(build_statistics_lines(items))
    lines.extend(build_category_lines(items,categories))
    lines.extend(build_history_lines(logs))
    
    with REPORT_FILE.open("w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines) + "\n")
        file.flush()
        os.fsync(file.fileno())
        
    print(f'สร้างรายงานแล้ว: {REPORT_FILE}')

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

def add_category() -> None:
    raw_id = input('รหัสหมวดหมู่: ').strip()
    
    if not raw_id.isascii() or not raw_id.isdecimal():
        print('รหัสหมวดหมู่ต้องเป็นเลขจำนวนเต็ม')
        return
    
    category_id = int(raw_id)
    if not 1 <= category_id <= 0xFFFFFFFF:
        print("กรุณาระบุรหัสหมวดหมู่ให้ถูกต้อง")
        return

    categories = read_records(CATEGORY_FILE, CATEGORY_STRUCT)
    if any(record[0] == category_id for record in categories):
        print("รหัสหมวดหมู่นี้มีอยู่แล้ว")
        return
    
    name = input("ชื่อหมวดหมู่: ").strip()
    if not name:
        print("ชื่อหมวดหมู่ห้ามว่าง")
        return
    
    description = input("รายละเอียดหมวดหมู่: ")
    
    try:
        record = (
            category_id,
            encode_fixed(name, 128, "ชื่อหมวดหมู่"),
            encode_fixed(description, 256, "รายละเอียด"),
            1,
        )
    except ValueError as error:
        print(error)
        return
    
    append_record(CATEGORY_FILE, CATEGORY_STRUCT, record)
    print("บันทึกหมวดหมู่แล้ว")

def input_uint32(label: str, minimum: int = 0) -> int:
    raw = input(label).strip()
    if not raw.isascii() or not raw.isdecimal():
        raise ValueError(f"{label}ต้องเป็นจำนวนเต็ม")
    value = int(raw)
    if not minimum <= value <= 0xFFFFFFFF:
        raise ValueError(f"{label}ต้องอยู่ระหว่าง {minimum} ถึง 4294967295")
    return value

def add_item() -> None:
    categories = [
        record for record in read_records(CATEGORY_FILE, CATEGORY_STRUCT)
        if record[3] == 1
    ]
    if not categories:
        print("กรุณาเพิ่มหมวดหมู่ก่อนเพิ่มพัสดุ")
        return

    print("หมวดหมู่ที่ใช้ได้:")
    for category in categories:
        print(f"  {category[0]}: {decode_fixed(category[1])}")

    try:
        item_id = input_uint32("รหัสพัสดุ: ", minimum=1)
        items = read_records(ITEM_FILE, ITEM_STRUCT)
        if any(record[0] == item_id for record in items):
            raise ValueError("รหัสพัสดุนี้มีอยู่แล้ว")

        category_id = input_uint32("รหัสหมวดหมู่: ", minimum=1)
        if not any(record[0] == category_id for record in categories):
            raise ValueError("ไม่พบรหัสหมวดหมู่ที่ใช้งานอยู่")

        name = input("ชื่อพัสดุ: ").strip()
        unit = input("หน่วยนับ: ").strip()
        location = input("ตำแหน่งจัดเก็บ: ").strip()
        if not all((name, unit, location)):
            raise ValueError("ชื่อพัสดุ หน่วยนับ และตำแหน่งจัดเก็บห้ามว่าง")

        quantity = input_uint32("จำนวนคงเหลือ: ")
        reorder_level = input_uint32("จุดสั่งซื้อขั้นต่ำ: ")
        price_text = input("ราคาต่อหน่วย: ").strip()
        unit_price = float(price_text)
        if not math.isfinite(unit_price) or unit_price < 0:
            raise ValueError("ราคาต่อหน่วยต้องเป็นตัวเลขตั้งแต่ 0 ขึ้นไป")
        struct.pack("<f", unit_price)

        operator = input("ผู้บันทึก: ").strip()
        if not operator:
            raise ValueError("ชื่อผู้บันทึกห้ามว่าง")

        item_record = (
            item_id, category_id,
            encode_fixed(name, 128, "ชื่อพัสดุ"),
            encode_fixed(unit, 48, "หน่วยนับ"),
            encode_fixed(location, 48, "ตำแหน่งจัดเก็บ"),
            quantity, reorder_level, unit_price, 1,
        )
        logs = read_records(TRANSACTION_FILE, TRANSACTION_STRUCT)
        log_seq = max((record[1] for record in logs), default=0) + 1
        if log_seq > 0xFFFFFFFF:
            raise ValueError("ลำดับประวัติเต็มแล้ว")
        log_record = (
            int(time.time()), log_seq, 1, item_id, quantity, float(quantity),
            encode_fixed(operator, 64, "ผู้บันทึก"),
            encode_fixed("เพิ่มพัสดุ", 128, "หมายเหตุ"), 1,
        )
        ITEM_STRUCT.pack(*item_record)
        TRANSACTION_STRUCT.pack(*log_record)
    except (ValueError, OverflowError, struct.error) as error:
        print(f"ข้อมูลไม่ถูกต้อง: {error}")
        return

    append_record(ITEM_FILE, ITEM_STRUCT, item_record)
    append_record(TRANSACTION_FILE, TRANSACTION_STRUCT, log_record)
    print("บันทึกพัสดุและประวัติแล้ว")

def update_item_name() -> None:
    try:
        item_id = input_uint32("รหัสพัสดุที่จะแก้ไข: ", minimum=1)
        found = find_active_item(item_id)
        if found is None:
            print("ไม่พบพัสดุที่ใช้งานอยู่")
            return
        
        index, old_record = found
        print(f"ชื่อเดิม: {decode_fixed(old_record[2])}")
        
        new_name = input("ชื่อใหม่: ").strip()
        if not new_name:
            raise ValueError("ชื่อใหม่ห้ามว่าง")
        
        operator = input("ผู้แก้ไข: ").strip()
        if not operator:
            raise ValueError("ชื่อผู้แก้ไขห้ามว่าง")
        
        updated = list(old_record)
        updated[2] = encode_fixed(new_name, 128, "ชื่อพัสดุ")
        updated = tuple(updated)
        
        logs = read_records(TRANSACTION_FILE, TRANSACTION_STRUCT)
        log_seq = max((row[1] for row in logs), default=0) + 1
        if log_seq > 0xFFFFFFFF:
            raise ValueError("ลำดับประวัติเต็มแล้ว")

        log_record = (
            int(time.time()), log_seq, 2, item_id, 0,
            float(old_record[5]),
            encode_fixed(operator, 64, "ผู้แก้ไข"),
            encode_fixed("แก้ไขชื่อพัสดุ", 128, "หมายเหตุ"),
            1,
        )

        ITEM_STRUCT.pack(*updated)
        TRANSACTION_STRUCT.pack(*log_record)
    except (ValueError, OverflowError, struct.error) as error:
        print(f"ข้อมูลไม่ถูกต้อง: {error}")
        return

    write_record_at(ITEM_FILE, ITEM_STRUCT, index, updated)
    append_record(TRANSACTION_FILE, TRANSACTION_STRUCT, log_record)
    print("แก้ไขชื่อพัสดุแล้ว")

def delete_item() -> None:
    try:
        item_id = input_uint32("รหัสพัสดุที่จะลบ: ", minimum=1)
        found = find_active_item(item_id)
        if found is None:
            print("ไม่พบพัสดุที่ใช้งานอยู่")
            return
        
        index, old_record = found
        print(f"ชื่อพัสดุ: {decode_fixed(old_record[2])}")

        confirm = input("ยืนยันการลบ? (y/N): ").strip().lower()
        if confirm != "y":
            print("ยกเลิกการลบ")
            return

        operator = input("ผู้ลบ: ").strip()
        if not operator:
            raise ValueError("ชื่อผู้ลบห้ามว่าง")

        deleted = list(old_record)
        deleted[8] = 0
        deleted = tuple(deleted)

        logs = read_records(TRANSACTION_FILE, TRANSACTION_STRUCT)
        log_seq = max((row[1] for row in logs), default=0) + 1
        if log_seq > 0xFFFFFFFF:
            raise ValueError("ลำดับประวัติเต็มแล้ว")

        log_record = (
            int(time.time()), log_seq, 3, item_id, 0,
            float(old_record[5]),
            encode_fixed(operator, 64, "ผู้ลบ"),
            encode_fixed("ลบพัสดุ", 128, "หมายเหตุ"),
            0,
        )

        ITEM_STRUCT.pack(*deleted)
        TRANSACTION_STRUCT.pack(*log_record)
    except (ValueError, OverflowError, struct.error) as error:
        print(f"ข้อมูลไม่ถูกต้อง: {error}")
        return

    write_record_at(ITEM_FILE, ITEM_STRUCT, index, deleted)
    append_record(TRANSACTION_FILE, TRANSACTION_STRUCT, log_record)
    print("ลบพัสดุแล้ว")   

def receive_item() -> None:
    try:
        item_id = input_uint32("รหัสพัสดุที่จะรับเข้า: ", minimum=1)
        found = find_active_item(item_id)
        if found is None:
            print("ไม่พบพัสดุที่ใช้งานอยู่")
            return

        index, old_record = found
        amount = input_uint32("จำนวนที่รับเข้า: ", minimum=1)
        new_quantity = old_record[5] + amount
        if new_quantity > 0xFFFFFFFF:
            raise ValueError("จำนวนคงเหลือเกินขนาดที่เก็บได้")
        
        operator = input('ผู้รับเข้า: ').strip()
        if not operator:
            raise ValueError("ชื่อผู้รับเข้าห้ามว่าง")
        note = input("หมายเหตุ (เว้นว่างได้): ")
        
        updated = list(old_record)
        updated[5] = new_quantity
        updated = tuple(updated)
        
        logs = read_records(TRANSACTION_FILE, TRANSACTION_STRUCT)
        log_seq = max((row[1] for row in logs), default=0) + 1
        if log_seq > 0xFFFFFFFF:
            raise ValueError("ลำดับประวัติเต็มแล้ว")
        
        log_record = (
            int(time.time()), log_seq, 4, item_id, amount,
            float(new_quantity),
            encode_fixed(operator, 64, "ผู้รับเข้า"),
            encode_fixed(note, 128, "หมายเหตุ"),
            1,
        )
        
        ITEM_STRUCT.pack(*updated)
        TRANSACTION_STRUCT.pack(*log_record)
    except (ValueError ,OverflowError, struct.error) as error:
        print(f'ข้อมูลไม่ถูกต้อง: {error}')
        return
    
    write_record_at(ITEM_FILE, ITEM_STRUCT, index, updated)
    append_record(TRANSACTION_FILE, TRANSACTION_STRUCT, log_record)
    print(f"รับพัสดุเข้าแล้ว คงเหลือ {new_quantity}")

def issue_item() -> None:
    try:
        item_id = input_uint32("รหัสพัสดุที่จะเบิก: ", minimum=1)
        found = find_active_item(item_id)
        if found is None:
            print("ไม่พบพัสดุที่ใช้งานอยู่")
            return

        index, old_record = found
        amount = input_uint32("จำนวนที่เบิก: ", minimum=1)
        if amount > old_record[5]:
            raise ValueError("จำนวนที่เบิกมากกว่าจำนวนคงเหลือ")

        new_quantity = old_record[5] - amount
        operator = input("ผู้เบิก: ").strip()
        if not operator:
            raise ValueError("ชื่อผู้เบิกห้ามว่าง")
        note = input("หมายเหตุ (เว้นว่างได้): ")

        updated = list(old_record)
        updated[5] = new_quantity
        updated = tuple(updated)

        logs = read_records(TRANSACTION_FILE, TRANSACTION_STRUCT)
        log_seq = max((row[1] for row in logs), default=0) + 1
        if log_seq > 0xFFFFFFFF:
            raise ValueError("ลำดับประวัติเต็มแล้ว")

        log_record = (
            int(time.time()), log_seq, 5, item_id, amount,
            float(new_quantity),
            encode_fixed(operator, 64, "ผู้เบิก"),
            encode_fixed(note, 128, "หมายเหตุ"),
            1,
        )

        ITEM_STRUCT.pack(*updated)
        TRANSACTION_STRUCT.pack(*log_record)
    except (ValueError, OverflowError, struct.error) as error:
        print(f"ข้อมูลไม่ถูกต้อง: {error}")
        return

    write_record_at(ITEM_FILE, ITEM_STRUCT, index, updated)
    append_record(TRANSACTION_FILE, TRANSACTION_STRUCT, log_record)
    print(f"เบิกพัสดุแล้ว คงเหลือ {new_quantity}")

def view_all_categories() -> None:
    categories = read_records(CATEGORY_FILE, CATEGORY_STRUCT)
    print("\n=== หมวดหมู่ ===")
    if not categories:
        print("ยังไม่มีข้อมูลหมวดหมู่")
        return

    for category in categories:
        status = "Active" if category[3] == 1 else "Deleted"
        print(f"\nรหัสหมวดหมู่: {category[0]} | สถานะ: {status}")
        print(f"ชื่อ: {decode_fixed(category[1])}")
        print(f"รายละเอียด: {decode_fixed(category[2])}")

def view_all_items() -> None:
    items = read_records(ITEM_FILE, ITEM_STRUCT)
    print("\n=== พัสดุ ===")
    if not items:
        print("ยังไม่มีข้อมูลพัสดุ")
        return
    
    category_names = {
        record[0]: decode_fixed(record[1])
        for record in read_records(CATEGORY_FILE, CATEGORY_STRUCT)
    }
    
    for item in items:
        status = "Active" if item[8] == 1 else "Deleted"
        print(f"\nรหัสพัสดุ: {item[0]} | สถานะ: {status}")
        print(f"หมวดหมู่: {category_names.get(item[1], 'ไม่พบหมวดหมู่')}")
        print(f"ชื่อ: {decode_fixed(item[2])}")
        print(f"หน่วยนับ: {decode_fixed(item[3])}")
        print(f"ตำแหน่ง: {decode_fixed(item[4])}")
        print(f"จำนวนคงเหลือ: {item[5]}")
        print(f"จุดสั่งซื้อขั้นต่ำ: {item[6]}")
        print(f"ราคาต่อหน่วย: {item[7]:.2f} บาท")

def view_one_item() -> None:
    try:
        item_id = input_uint32("รหัสพัสดุที่ต้องการดู: ", minimum=1)
    except ValueError as error:
        print(error)
        return
    items = read_records(ITEM_FILE, ITEM_STRUCT)
    item = next((record for record in items if record[0] == item_id), None)
    
    if item is None:
        print("ไม่พบรหัสพัสดุ")
        return
    
    print("\n".join(build_item_table([item])))
    print(f"ตำแหน่งจัดเก็บ: {decode_fixed(item[4])}")
    print(f"จุดสั่งซื้อขั้นต่ำ: {item[6]}")

def view_filtered_items() -> None:
    try:
        category_id = input_uint32("รหัสหมวดหมู่ที่ต้องการดู: ", minimum=1)
    except ValueError as error:
        print(error)
        return

    categories = read_records(CATEGORY_FILE, CATEGORY_STRUCT)
    if not any(category[0] == category_id for category in categories):
        print("ไม่พบรหัสหมวดหมู่")
        return
    
    items = [
        item for item in read_records(ITEM_FILE, ITEM_STRUCT)
        if item[1] == category_id and item[8] == 1
    ]
    
    if not items:
        print("ไม่มีพัสดุที่ใช้งานอยู่ในหมวดหมู่นี้")
        return
    
    print("\n".join(build_item_table(items)))

def view_summary() -> None:
    items = read_records(ITEM_FILE, ITEM_STRUCT)
    categories = read_records(CATEGORY_FILE, CATEGORY_STRUCT)
    
    lines = build_summary_lines(items)
    lines.extend(build_statistics_lines(items))
    lines.extend(build_category_lines(items, categories))
    
    print("\n".join(lines))

def main():
    while True:
        print("\n=== ระบบคลังพัสดุ ===")
        print("1) เพิ่มข้อมูล")
        print("2) แก้ไขพัสดุ")
        print("3) ลบพัสดุ")
        print("4) ดูข้อมูล")
        print("5) สร้าง report.txt")
        print("6) รับพัสดุเข้า")
        print("7) เบิกพัสดุออก")
        print("0) ออกจากโปรแกรม")

        choice = input("เลือกเมนู: ").strip()

        if choice == "0":
            generate_report()
            print("ปิดโปรแกรม")
            break
        elif choice == "1":
            print("1) เพิ่มหมวดหมู่")
            print("2) เพิ่มพัสดุ")
            sub_choice = input("เลือกเมนูย่อย: ").strip()

            if sub_choice == "1":
                add_category()
            elif sub_choice == "2":
                add_item()
            else:
                print("เมนูย่อยไม่ถูกต้อง")
        elif choice == "4":
            print("1) ดูพัสดุรายการเดียว")
            print("2) ดูข้อมูลทั้งหมด")
            print("3) ดูพัสดุตามหมวดหมู่")
            print("4) ดูสถิติโดยสรุป")
            view_choice = input("เลือกเมนูย่อย: ").strip()

            if view_choice == "1":
                view_one_item()
            elif view_choice == "2":
                view_all_categories()
                view_all_items()
            elif view_choice == "3":
                view_filtered_items()
            elif view_choice == "4":
                view_summary()
            else:
                print("เมนูย่อยไม่ถูกต้อง")
        elif choice == "2":
            update_item_name()
        elif choice == "3":
            delete_item()
        elif choice == "6":
            receive_item()
        elif choice == "7":
            issue_item()
        elif choice == "5":
            generate_report()
        else:
            print("กรุณาเลือกหมายเลขเมนูที่แสดง")


if __name__ == "__main__":
    main()
