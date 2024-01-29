import asyncio
import csv
import io

# import json
import logging
import os
import re
import sys
from pathlib import Path

import toml
from dotenv import load_dotenv
from flask import (
    Flask,
    copy_current_request_context,
    flash,
    render_template,
    request,
    send_file,
)
from flask_bootstrap import Bootstrap5  # type: ignore

from receiptparser.doc_intel_receipt import analyze_receipt

# from receiptparser.extractors import (
#     FileNameError,
# )

load_dotenv()

UPLOAD_LOCATION = os.getenv("UPLOAD_LOCATION", "uploads")

app = Flask(__name__)
Bootstrap5(app)

logging.basicConfig(filename="app.log", level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))


# Predefined list of vendors
# vendors = ['Vendor A', 'Vendor B', 'Vendor C']
def get_vendors_from_config(config):
    return config["vendors"]["list"]


config_path = Path("config.toml")
config = toml.load(config_path)

app.config["SECRET_KEY"] = "123456"  # noqa: S105

vendors = get_vendors_from_config(config)

upload_location = Path(UPLOAD_LOCATION)

upload_location.mkdir(parents=True, exist_ok=True)
app.config["ALLOWED_EXTENSIONS"] = config["upload"]["allowed_file_types"]


def allowed_file(filename):
    logger.debug(f"filename.rsplit(\".\", 1): {filename.rsplit('.', 1)}")
    logger.debug(f"filename.rsplit(\".\", 1)[1]: {filename.rsplit('.', 1)[1]}")
    logger.debug(
        f"filename.rsplit(\".\", 1)[1].lower(): {filename.rsplit('.', 1)[1].lower()}",
    )
    logger.debug(
        f"app.config[\"ALLOWED_EXTENSIONS\"]: {app.config['ALLOWED_EXTENSIONS']}",
    )
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )  # noqa: E501


@app.route("/", methods=["GET", "POST"])
def upload_file():  # noqa: C901
    processed_data = None
    if request.method == "POST":
        # TODO: re-enable `selected_vendor`
        # selected_vendor = request.form["vendor"]
        # Process the uploaded file or perform any other actions with the selected vendor  # noqa: E501
        # For example, you can save the file and do further processing
        uploaded_file = request.files["file"]
        if uploaded_file and allowed_file(uploaded_file.filename):
            file_path = upload_location / uploaded_file.filename
            logger.debug(f"Upload filepath: {file_path}")
            uploaded_file.save(file_path)
            filename = uploaded_file.filename
            items = []

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            @copy_current_request_context
            async def process_receipt(file_path):
                nonlocal processed_data

                try:
                    receipts = await loop.run_in_executor(
                        None,
                        analyze_receipt,
                        file_path,
                    )
                    for _receipt_idx, receipt in enumerate(receipts.documents):
                        logger.info(f"Receipt Type: {receipt.doc_type}")
                        # json_object = json.dumps(receipt, indent=4)
                        # with Path.open(upload_location / filename, ".json") as json_file:  # noqa: E501
                        #     json_file.write(json_object)
                        merchant_name = receipt.fields.get("MerchantName")
                        if merchant_name:
                            logger.info(
                                f"Merchant Name: {merchant_name.value_string} with "
                                f"{merchant_name.confidence:.1%} confidence.",
                            )
                        transaction_date = receipt.fields.get("TransactionDate")
                        if transaction_date:
                            logger.info(
                                f"Transaction Date {transaction_date.value_string} with"
                                f" {transaction_date.confidence:%1} confidence.",
                            )

                        items = receipt.fields.get("Items").value_array
                        if receipt.fields.get("Items"):
                            for _item_idx, item in enumerate(
                                items,
                            ):
                                item_object = item.value_object
                                product_code = item_object.get(
                                    "ProductCode",
                                ).value_string
                                logger.debug(
                                    f"Item {item_object} has product code "
                                    f"{product_code}.",
                                )
                                description = item_object.get(
                                    "Description",
                                ).value_string
                                total_price = item_object.get(
                                    "TotalPrice",
                                ).value_currency.amount
                                costco_tax_pattern = r"\s\d+.\d{2}\s([Y,N])?$"
                                matches = re.match(
                                    costco_tax_pattern,
                                    item.content,
                                )
                                taxable_status = matches[0] == "Y" if matches else False
                                item_dict = {
                                    "product_code": product_code,
                                    "description": description,
                                    "total_price": total_price,
                                    "taxable": taxable_status,
                                }
                                items.append(item_dict)
                except Exception:
                    raise
                    # processed_data = None
                    # flash(
                    #     f"Filename `{filename}` does not match pattern "
                    #     '"YYYYMMDD vendor 123.45".',
                    # )
                    # return render_template(
                    #     "upload.html",
                    #     vendors=vendors,
                    #     processed_data=processed_data,
                    # )

            loop.run_until_complete(process_receipt(file_path))
        else:
            flash(
                f"Invalid file type. Allowed file types are: {', '.join(app.config['ALLOWED_EXTENSIONS'])}",  # noqa: E501
            )
            return render_template(
                "upload.html",
                vendors=vendors,
                processed_data=processed_data,
            )

        match request.form["output_type"]:
            case "html":
                processed_data = processed_data.to_html(
                    classes="table table-striped",
                    header=True,
                    index=False,
                )
                return render_template(
                    "upload.html",
                    vendors=vendors,
                    processed_data=processed_data,
                )
            case "csv":
                keys = items[0].keys()

                writer = csv.DictWriter(fieldnames=keys)
                writer.writeheader()
                writer.writerows(items)
                # //processed_data = processed_data.to_csv(index=False)
                output_filename = f"{filename}"
                return send_file(
                    io.BytesIO(writer),
                    mimetype="text/csv",
                    as_attachment=True,
                    download_name=f"{output_filename}.csv",
                )

    return render_template(
        "upload.html",
        vendors=vendors,
        processed_data=processed_data,
    )


# @app.route("/get-csv")
# def get_csv():


if __name__ == "__main__":
    app.run(debug=True)
