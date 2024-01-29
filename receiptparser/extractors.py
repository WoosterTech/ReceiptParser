import logging
import re
import sys
from datetime import date
from datetime import datetime as dt
from decimal import Decimal
from pathlib import Path

import cv2
import fitz
import pytesseract
from pandas import DataFrame

logging.basicConfig(filename="extractor.log", level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

# from pytesseract import Output

# import list
# from extract import ReceiptItem


class FileNameError(ValueError):
    def __init__(self, filename: str = "", *args: object) -> None:
        super().__init__(*args)
        self.filename = filename


class ReceiptItem:
    """Single line of receipt.

    :param identifier: UPC/Item Number/Other identifier
    :type identifier: str
    :param description: Description of item
    :type description: str
    :param price: Price of line/item
    :type price: Decimal
    :param category: Used to identify if taxable or not
    :type category: str
    """

    def __init__(
        self,
        identifier: str,
        description: str,
        price: Decimal,
        category: str | None,
        tax_code: str,
    ):
        self.identifier = identifier
        self.description = description
        self.price = price
        self.category = category
        self.tax_code = tax_code


class CostcoReceiptItem(ReceiptItem):
    def __init__(
        self,
        identifier: str,
        description: str,
        price: Decimal,
        category: str,
        tax_code: str,
        original_price: Decimal = None,
        coupon: Decimal = None,
    ):
        super().__init__(identifier, description, price, category, tax_code)
        self.coupon = coupon
        self.original_price = original_price
        self.price = (
            self.final_price() if (self.coupon and self.original_price) else self.price
        )

    def final_price(self):
        return self.original_price - self.coupon


class ReceiptObject:
    def __init__(
        self,
        date: date = None,
        upload_filename: str = "",
        receipt_total: Decimal = 0,
        items=None,
        tax_rate: float = 0.0089,
        vendor: str = "",
    ):
        self.date = date
        self.upload_filename = str(Path(upload_filename).stem)
        self.receipt_total = receipt_total
        self.items = items
        self.tax_rate = tax_rate
        self.vendor = vendor

        # if isinstance(self.upload_filename, Path):
        #     self.upload_filename = str(self.upload_filename.stem)

        if self.upload_filename:
            try:
                self.set_metadata_from_filename()
            except FileNameError:
                raise

    def set_items(self, filepath: Path):
        match self.vendor.lower():
            case "costco":
                receipt_text = get_costco_text(filepath)
                matches = get_receipt_lines(receipt_text, REGEX_PATTERNS["costco"])
                items = [format_costco_line(match) for match in matches]
                self.items = DataFrame.from_dict(items)
            case "target":
                pass
            case "walmart":
                pass
            case _:
                raise ValueError(
                    f"Missing or invalid vendor: {self.vendor if self.vendor else 'none'}",  # noqa: E501
                )

        return self.items

    def set_metadata_from_filename(self):
        try:
            metadata_dict = grab_receipt_metadata(str(self.upload_filename))
        except FileNameError:
            raise
        self.date = (
            metadata_dict.get("transaction_date") if not self.date else self.date
        )
        self.receipt_total = (
            metadata_dict.get("transaction_total")
            if not self.receipt_total
            else self.receipt_total
        )


def grab_receipt_metadata(filename: str):
    """Use filename to determine transaction date, vendor, and transaction total.

    Args:
        filename (str): Uploaded file filename; no folder if string

    Returns:
        dict: {
            "transaction_date": date,
            "vendor": str,
            "transaction_total": Decimal
        }
    """
    if isinstance(filename, str):
        # "YYYYMMDD vendor xx.xx"
        pattern = r"(\d{8})\s+([a-zA-Z\s]+)\s+(\d+\.\d{2})"
        # pattern = r"(\d{8})\s(\w+)\s(\d+.\d{0,2})"

        logging.debug(f"Pattern for filename regex: {pattern}")

        matches = re.match(pattern, filename)

        logging.debug(f"Filename regex matches: {matches}")

        try:
            receipt_date = matches[1]
            receipt_vendor = matches[2]
            receipt_total = matches[3]
        except TypeError:
            raise FileNameError() from TypeError

        receipt_date = dt.strptime(receipt_date, "%Y%m%d")

        return {
            "transaction_date": receipt_date,
            "vendor": receipt_vendor,
            "transaction_total": receipt_total,
        }
    else:
        raise ValueError(f"Filename must be a string, not {type(filename)}")


def get_receipt_lines(text: str, pattern: str):
    matches = re.findall(pattern, text)
    lines = []

    for match in matches:
        lines.append(match)

    return lines


def fix_negative(price: str) -> Decimal:
    new_price = f"-{price.rstrip('-')}" if "-" in price else price

    return Decimal(new_price)


def export_raw_data(data: str, file_prefix: str, filepath: str):
    filename = f"{file_prefix}_{dt.now().strftime('%Y%m%d%H%M%S')}.txt"
    filename = Path(filepath, filename)
    try:
        with Path.open(filename, "w") as file:
            file.write(data)
    except TypeError:
        text_str = ""
        for x in data:
            text_str = f"{text_str}{x}\n"
        # text_str += {f"{x}\n" for x in data}
        with Path.open(filename, "w") as file:
            file.write(text_str)
    except Exception:
        raise


def get_costco_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    full_text = ""

    for page_num in range(len(doc)):
        page = doc[page_num]
        full_text += page.get_text()

    return full_text


def format_costco_line(line: tuple) -> dict:
    item_code, item_number, description, price, tax_code = line
    return {
        "identifier": item_number,
        "description": description,
        "category": item_code,
        "tax_code": tax_code,
        "price": price,
    }


REGEX_PATTERNS = {
    "costco": r"(\S?)\s+(\d+)\s+(.+?)\s+(-?\d+\.\d{2}-?)[^\S\n]?(\S?)",
    "target": r"(\d+)\s(.+?)\s+(\w+)\s+?\$(\d+?\.\d+)",
    "walmart": r"(.+?)\s(\d{12})\s(.)?(?:\s)?(\d+(?:\.)?(?:\d+)?)\n",
}


# def costco_extract_info(pdf_path: Path) -> list[ReceiptItem]:
#     # doc = fitz.open(pdf_path)
#     receipt_items = DataFrame

#     full_text = get_costco_full_text(pdf_path)

#         # Regular expression to extract item lines
#         pattern = r"(\S?)\s+(\d+)\s+(.+?)\s+(-?\d+\.\d{2}-?)[^\S\n]?(\S?)"
#         # pattern = r"(\S*)\n(\d+)\n((?:(?!\n\S+ \d+\.\d{2}).)*)\n(-?\d+\.\d{2}-?|/0)"

#         matches = re.findall(pattern, text)

#         # try:
#         #     export_raw_data(matches, "matches", pdf_path.parent)
#         # except Exception as e:
#         #     print("Could not export matches:", e)

#         for match in matches:
#             item_code, item_number, description, price, tax_code = match
#             price = fix_negative(price)
#             # subtotal += price
#             receipt_item = CostcoReceiptItem(
#                 item_number,
#                 description,
#                 price,
#                 item_code,
#                 tax_code,
#             )
#             receipt_items.append(receipt_item)

#     return receipt_items


def target_extract_info(pdf_path) -> list[ReceiptItem]:
    doc = fitz.open(pdf_path)
    receipt_items = []
    # subtotal = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        print(text)

        pattern = r"(\d+)\s(.+?)\s+(\w+)\s+?\$(\d+?\.\d+)"
        matches = re.findall(pattern, text)

        for match in matches:
            item_number, description, tax_code, price = match
            price = fix_negative(price)
            # subtotal += price
            receipt_item = ReceiptItem(
                item_number,
                description,
                price,
                category=None,
                tax_code=tax_code,
            )
            receipt_items.append(receipt_item)

    return receipt_items


def walmart_extract_info(pdf_path: Path) -> list[ReceiptItem]:
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    path = str(pdf_path)

    img = cv2.imread(path)

    text = pytesseract.image_to_string(img)

    # print(text)

    pattern = r"(.+?)\s(\d{12})\s(.)?(?:\s)?(\d+(?:\.)?(?:\d+)?)\n"
    matches = re.findall(pattern, text)

    receipt_items = []
    for match in matches:
        if len(match) == 4:
            description, item_number, tax_code, price = match
        elif len(match) == 3:
            description, item_number, price = match
            tax_code = None

        price = fix_negative(price)
        # subtotal += price
        receipt_item = ReceiptItem(
            item_number,
            description,
            price,
            category=None,
            tax_code=tax_code,
        )
        receipt_items.append(receipt_item)

    return receipt_items
