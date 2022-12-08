from extensions.display_image_crosshair_graph import ImageCrossHairGraph
from extensions.models.api import ImageCrossHairGraphModel
from karabo.native import Configurable, Node, VectorInt32
from karabogui.api import DeviceProxy, PropertyProxy, build_binding
from karabogui.conftest import gui_app
from karabogui.controllers.display.tests.image import get_output_node


class PipelineData(Configurable):
    output = Node(get_output_node(), displayType="OutputChannel")
    crosshair_pos = VectorInt32(displayType="crosshair")


def test_basics(gui_app: gui_app, mocker):
    schema = PipelineData().getDeviceSchema()
    binding = build_binding(schema)
    root_proxy = DeviceProxy(binding=binding, device_id="TestDeviceId")
    proxy = PropertyProxy(root_proxy=root_proxy, path='output.data.image')
    controller = ImageCrossHairGraph(proxy=proxy,
                                     model=ImageCrossHairGraphModel())
    controller.create(None)
    controller.set_read_only(False)
    # No crosshairs by default
    assert not controller._crosshairs

    # add a crosshair
    position_proxy = PropertyProxy(root_proxy=root_proxy, path="crosshair_pos")
    assert position_proxy.binding
    position_proxy.value = (100, 200)
    assert controller.visualize_additional_property(position_proxy)
    assert len(controller._crosshairs) == 1
    assert controller._crosshairs[0] == position_proxy

    # Image clicked
    dialog_path = "extensions.display_image_crosshair_graph.QMessageBox"
    pos = (40, 190)
    msg_box = mocker.patch(dialog_path)
    msg_box().exec.return_value = msg_box.Ok
    controller._image_clicked(*pos)
    value = controller._crosshairs[0].edit_value
    assert all(value == pos)
