import io
import logging
import sys
from pathlib import Path

import toml
from flask import Flask, flash, render_template, request, send_file
from flask_bootstrap import Bootstrap

from receiptparser.extractors import (
    FileNameError,
    ReceiptObject,
)

app = Flask(__name__)
Bootstrap(app)

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

upload_location = Path(config["upload"]["location"])

upload_location.mkdir(parents=True, exist_ok=True)
app.config["ALLOWED_EXTENSIONS"] = config["upload"]["allowed_file_types"]


def allowed_file(filename):
    logger.debug(f"filename.rsplit(\".\", 1): {filename.rsplit('.', 1)}")
    logger.debug(f"filename.rsplit(\".\", 1)[1]: {filename.rsplit('.', 1)[1]}")
    logger.debug(f"filename.rsplit(\".\", 1)[1].lower(): {filename.rsplit('.', 1)[1].lower()}")
    logger.debug(f"app.config[\"ALLOWED_EXTENSIONS\"]: {app.config['ALLOWED_EXTENSIONS']}")
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


@app.route("/", methods=["GET", "POST"])
def upload_file():
    processed_data = None
    if request.method == "POST":
        selected_vendor = request.form["vendor"]
        # Process the uploaded file or perform any other actions with the selected vendor  # noqa: E501
        # For example, you can save the file and do further processing
        uploaded_file = request.files["file"]
        if uploaded_file and allowed_file(uploaded_file.filename):
            file_path = upload_location / uploaded_file.filename
            logger.debug(f"Upload filepath: {file_path}")
            uploaded_file.save(file_path)
            filename = uploaded_file.filename
            try:
                receipt_obj = ReceiptObject(vendor=selected_vendor, upload_filename=filename)
                processed_data = receipt_obj.set_items(file_path)
            except FileNameError:
                processed_data = None
                flash(f'Filename `{filename}` does not match pattern "YYYYMMDD vendor 123.45".')
                return render_template(
                    "upload.html",
                    vendors=vendors,
                    processed_data=processed_data,
                )
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
                processed_data = processed_data.to_csv(index=False)
                output_filename = f"{receipt_obj.upload_filename}"
                return send_file(
                    io.BytesIO(processed_data.encode("utf-8")),
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
