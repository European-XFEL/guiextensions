from extensions.display_file_uploader import DisplayFileUploader
from karabo.native import Bool, Configurable, Hash, Node, String
from karabogui.conftest import gui_app
from karabogui.testing import get_class_property_proxy, set_proxy_hash


class UploaderNode(Configurable):
    info = String()
    allowed = Bool(defaultValue=True)


class Device(Configurable):
    uploader = Node(UploaderNode, displayedName="My Uploader")


def test_uploader_widget(gui_app: gui_app):
    schema = Device.getClassSchema()
    proxy = get_class_property_proxy(schema, "uploader")
    controller = DisplayFileUploader(proxy=proxy)
    controller.create(None)

    assert controller.widget.isEnabled()
    assert controller.widget.toolTip() == ""

    values = {
        "allowed": False,
        "info": "Operation",
    }

    set_proxy_hash(proxy, Hash("uploader", Hash(values)))
    assert not controller.widget.isEnabled()
    assert controller.widget.toolTip() == "Operation"
