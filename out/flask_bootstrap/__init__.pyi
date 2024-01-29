from _typeshed import Incomplete
from wtforms import BooleanField

CDN_BASE: str

def is_hidden_field_filter(field): ...
def raise_helper(message) -> None: ...
def get_table_titles(data, primary_key, primary_key_title): ...

class _Bootstrap:
    bootstrap_version: Incomplete
    jquery_version: Incomplete
    popper_version: Incomplete
    bootstrap_css_integrity: Incomplete
    bootstrap_js_integrity: Incomplete
    jquery_integrity: Incomplete
    popper_integrity: Incomplete
    static_folder: Incomplete
    bootstrap_css_filename: str
    bootstrap_js_filename: str
    jquery_filename: str
    popper_filename: str
    def __init__(self, app: Incomplete | None = None) -> None: ...
    def init_app(self, app) -> None: ...
    def load_css(
        self,
        version: Incomplete | None = None,
        bootstrap_sri: Incomplete | None = None,
    ): ...
    def load_js(
        self,
        version: Incomplete | None = None,
        jquery_version: Incomplete | None = None,
        popper_version: Incomplete | None = None,
        with_jquery: bool = True,
        with_popper: bool = True,
        bootstrap_sri: Incomplete | None = None,
        jquery_sri: Incomplete | None = None,
        popper_sri: Incomplete | None = None,
        nonce: Incomplete | None = None,
    ): ...

class Bootstrap4(_Bootstrap):
    bootstrap_version: str
    jquery_version: str
    popper_version: str
    bootstrap_css_integrity: str
    bootstrap_js_integrity: str
    jquery_integrity: str
    popper_integrity: str
    popper_name: str
    static_folder: str

class Bootstrap5(_Bootstrap):
    bootstrap_version: str
    popper_version: str
    bootstrap_css_integrity: str
    bootstrap_js_integrity: str
    popper_integrity: str
    popper_name: str
    static_folder: str

class Bootstrap(Bootstrap4):
    def __init__(self, app: Incomplete | None = None) -> None: ...

class SwitchField(BooleanField):
    def __init__(self, label: Incomplete | None = None, **kwargs) -> None: ...
