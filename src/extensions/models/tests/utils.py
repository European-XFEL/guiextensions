"""A basic place for model testing `utils`"""


def _geometry_traits():
    return {"x": 0, "y": 0, "height": 100, "width": 100}


def _assert_geometry_traits(model):
    traits = _geometry_traits()
    for name, value in traits.items():
        msg = f"Attribute {name} has the wrong value {value}"
        assert getattr(model, name) == value, msg
