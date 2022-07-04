import random
from enum import Enum
from time import sleep

from karabo.native import (
    AccessMode, Configurable, Float, Hash, MetricPrefix, String, Unit,
    VectorHash)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)

from ..display_networkx import NetworkX


class ConnectionType(Enum):
    P2P = "p2p"
    DAQ_SINK = "daq_sink"
    DAQ_SOURCE = "daq_source"


class ConnectionStatus(Enum):
    ACTIVE = "active"
    PASSIVE = "passive"
    OUTPUT_BROKEN = "output_broken"
    INPUT_BROKEN = "input_broken"
    UNCLEAR = "unclear"


class Nodelist(Configurable):
    originNode = String(accessMode=AccessMode.READONLY)
    destinationNode = String(accessMode=AccessMode.READONLY)
    connectionType = String(accessMode=AccessMode.READONLY)
    originType = String(accessMode=AccessMode.READONLY)
    destinationType = String(accessMode=AccessMode.READONLY)
    status = String(accessMode=AccessMode.READONLY)
    bytesTransferred = Float(accessMode=AccessMode.READONLY,
                             unitSymbol=Unit.BYTE,
                             metricPrefixSymbol=MetricPrefix.MEGA)


class Object(Configurable):
    nodes = VectorHash(rows=Nodelist, accessMode=AccessMode.READONLY,
                       displayType="NetworX")


# "Classes" we will mock and also filter on.
CAM_CLASS = "CAM"
DA_CLASS = "DA"
MDL_CLASS = "MDL"


def _create_values():
    # create nodes
    nodes = []
    classTypes = [MDL_CLASS, CAM_CLASS, DA_CLASS]
    for i in range(100):
        nodes.append(f"FOO_BAR_FOO/{random.choice(classTypes)}/DEVICE_{i}")
    # create connection entries
    rows = []
    for i in range(1000):
        node1 = random.choice(nodes)
        node2 = random.choice(nodes)
        while node1 == node2:
            node2 = random.choice(nodes)
        row = Hash()
        row["originNode"] = node1
        row["destinationNode"] = node2
        row["connectionType"] = "p2p"
        row["originType"] = random.choice([ConnectionType.P2P.value,
                                           ConnectionType.DAQ_SOURCE.value])
        row["destinationType"] = random.choice(
            [ConnectionType.P2P.value, ConnectionType.DAQ_SOURCE.value,
             ConnectionType.DAQ_SINK.value])
        row["status"] = random.choice(list(ConnectionStatus)).value
        row["bytesTransferred"] = random.random() * 1e3
        rows.append(row)
    return rows


class TestNetworkX(GuiTestCase):
    def setUp(self):
        super(TestNetworkX, self).setUp()

        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'nodes')

        self.controller = NetworkX(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    def test_graph_creation(self):
        data = _create_values()
        set_proxy_hash(self.proxy, Hash('nodes', data, ))
        nodes = self.controller.graphwidget.nodes.values()

        # general check on length
        unique_nodes = set()
        prevailent_types = {}
        for row in data:
            unique_nodes.add(row["originNode"])
            unique_nodes.add(row["destinationNode"])

            # we need to sort out the prevalent types here, as daq
            # types take priority
            ptype = prevailent_types.setdefault(row["originNode"],
                                                row["originType"])
            if "daq" in row["originType"]:
                if ptype != "daq_sink":
                    prevailent_types[row["originNode"]] = row["originType"]

            ptype = prevailent_types.setdefault(row["destinationNode"],
                                                row["destinationType"])
            if "daq" in row["destinationType"]:
                if ptype != "daq_sink":
                    prevailent_types[
                        row["destinationNode"]] = row["destinationType"]

        self.assertEqual(len(nodes), len(unique_nodes))
        # now test them individually
        for row in data:
            origin = row["originNode"]
            dest = row["destinationNode"]
            connection_type = row["connectionType"]  # not used currently
            origin_type = row["originType"]
            dest_type = row["destinationType"]
            status = row["status"]  # not updated currently
            bytes_transferred = row["bytesTransferred"]  # not used currently
            node_found = False
            edge_found = False
            for node in nodes:
                if node.label == origin:
                    for edge in node.edge_list:
                        if edge.dest_node().label == dest:
                            node_found = True
                            edge_found = True

                            self.assertEqual(node.group,
                                             prevailent_types[node.label])

                            self.assertEqual(
                                edge.dest_node().group,
                                prevailent_types[
                                    edge.dest_node().label])
                            break
            self.assertTrue(node_found)
            self.assertTrue(edge_found)

    def test_filters(self):
        data = _create_values()
        set_proxy_hash(self.proxy, Hash('nodes', data, ))
        self.controller.filter_ledit.setText(CAM_CLASS)
        self.controller.on_filter()
        self.controller.filter_ledit.setText(DA_CLASS)
        self.controller.on_filter()
        sleep(2)

        for idx in range(self.controller.filter_instances.count()):
            item = self.controller.filter_instances.itemAt(idx).widget()
            if item:
                self.assertTrue(item.is_active)

        nodes = self.controller.graphwidget.nodes.values()
        for node in nodes:
            visible = CAM_CLASS in node.label or DA_CLASS in node.label
            # we need to also check the direct edges
            for edge in node.edge_list:
                enode = edge.dest_node()
                visible |= CAM_CLASS in enode.label or DA_CLASS in enode.label
            self.assertEqual(visible, node.isVisible())

        # toggle one filter off
        for idx in range(self.controller.filter_instances.count()):
            item = self.controller.filter_instances.itemAt(idx).widget()
            if item and item.text() == CAM_CLASS:
                item.toggle_active()

        nodes = self.controller.graphwidget.nodes.values()
        for node in nodes:
            visible = DA_CLASS in node.label
            # we need to also check the direct edges
            for edge in node.edge_list:
                enode = edge.dest_node()
                visible |= DA_CLASS in enode.label
                enode = edge.source_node()
                visible |= DA_CLASS in enode.label

            self.assertEqual(visible, node.isVisible())

        # toggle again, and also remove one filter
            # toggle one filter off
            for idx in range(self.controller.filter_instances.count()):
                item = self.controller.filter_instances.itemAt(idx).widget()
                if item and item.text() == CAM_CLASS:
                    item.toggle_active()
                elif item and item.text() == DA_CLASS:
                    item.mouseDoubleClickEvent(None)

        nodes = self.controller.graphwidget.nodes.values()
        for node in nodes:
            visible = CAM_CLASS in node.label
            # we need to also check the direct edges
            for edge in node.edge_list:
                enode = edge.dest_node()
                visible |= CAM_CLASS in enode.label
                enode = edge.source_node()
                visible |= CAM_CLASS in enode.label

            self.assertEqual(visible, node.isVisible())

        # now remove all filters, all nodes are visible
        self.controller.on_clear_filter()
        nodes = self.controller.graphwidget.nodes.values()
        for node in nodes:
            self.assertTrue(node.isVisible())