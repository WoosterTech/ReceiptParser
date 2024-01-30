import os
from pathlib import Path

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("AZURE_DOC_INTEL_ENDPOINT")
KEY = os.getenv("AZURE_DOC_INTEL_KEY")


class MissingEnvironmentVariableError(Exception):
    pass


def analyze_receipt(filepath: Path | str):  # noqa: C901
    # "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/sample-invoice.pdf"\

    if not ENDPOINT:
        raise MissingEnvironmentVariableError('Missing "AZURE_DOC_INTEL_ENDPOINT"')
    if not KEY:
        raise MissingEnvironmentVariableError('Missing "AZURE_DOC_INTEL_KEY"')

    if not isinstance(filepath, Path):
        filepath = Path(filepath)

    doc_intel_client = DocumentIntelligenceClient(
        endpoint=ENDPOINT,
        credential=AzureKeyCredential(KEY),
    )

    with Path.open(filepath, "rb") as f:
        poller = doc_intel_client.begin_analyze_document(
            "prebuilt-receipt",
            analyze_request=f,
            locale="en-US",
            content_type="application/octet-stream",
        )
    receipts = poller.result()

    return receipts
