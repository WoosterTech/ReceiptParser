# from decimal import Decimal
import csv
from pathlib import Path
from time import sleep
from tkinter import Tk, filedialog

from extractors import costco_extract_info, target_extract_info, walmart_extract_info


def open_canceled(pdf_path: str):
    """Check to see if a file was selected and exit if not."""
    if not pdf_path:
        print("No file selected, closing...")
        sleep(2)
        exit(0)


def save_to_csv(receipt_items, csv_file):
    with Path.open(csv_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Item Number", "Description", "Price", "Tax Code"])
        # for item in receipt_items:
        #     writer.write
        writer.writerows(
            [
                (item.identifier, item.description, item.price, item.tax_code)
                for item in receipt_items
            ],
        )
        writer.writerow([])  # empty row

        subtotal = sum(item.price for item in receipt_items)
        writer.writerow(["Subtotal", "", "", f"${subtotal:.2f}"])


def get_vendor_name() -> str:
    vendor_list = [{"costco": "Costco"}, {"target": "Target"}, {"walmart": "Walmart"}]

    print("Choose vendor from list...\n")
    for vendor in vendor_list:
        print(vendor)
    vendor_str = str(input("Enter selection:\n")).lower()

    return vendor_str


if __name__ == "__main__":
    # Create Tkinter root window
    root = Tk()
    root.withdraw()  # Hide the root window

    # Prompt user for PDF receipt
    pdf_path = filedialog.askopenfilename(
        title="Please select the receipt to be parsed",
        filetypes=[("PDFs", "*.pdf"), ("Images", "*.png")],
    )
    open_canceled(pdf_path)

    pdf_path = Path(pdf_path)

    receipt_vendor = get_vendor_name()

    match receipt_vendor:
        case "costco":
            receipt_items = costco_extract_info(pdf_path)
        case "target":
            receipt_items = target_extract_info(pdf_path)
        case "walmart":
            receipt_items = walmart_extract_info(pdf_path)
        case _:
            raise ValueError("Invalid Vendor Choice")

    # pdf_directory = pdf_path.parent

    csv_file = Path(f"{pdf_path.parent}\\{pdf_path.stem}.csv")

    save_to_csv(receipt_items, csv_file)
    print(f"Data saved to {csv_file}")

    # for item in receipt_items:
    #     print(f"Description: {item.description}")
    #     print(f"Item Number: {item.identifier}")
    #     print(f"Price: ${item.price:.2f}")
    #     print(f"Item Code: {item.category}")
    #     print()
