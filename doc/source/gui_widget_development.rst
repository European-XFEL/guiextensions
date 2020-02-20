.. _gui-extensions-checklist:

==========================
Widget Developer Checklist
==========================

the following Classes needs to be created:

- The Scene MODEL of the widget
- The UNIT TESTS!
- The WIDGET CONTROLLER

if the Scene Model contains traits (i.e. needs to persist configuration data), the
following elements need to be added:

- The Scene Model WRITER
- The Scene Model READER


MODEL
=====

- add the MODEL to the `src/extensions/models/**APPROPRIATE**.py`
  file.

if the MODEL contains traits, the developer will add:

- the Scene Model WRITER to
  `src/extensions/models/**APPROPRIATE**.py`.
- the Scene Model READER to
  `src/extensions/models/**APPROPRIATE**.py`.
  The READER's version should be left **UNTOUCHED**.


WIDGET CONTROLLER
=================

- Add the WIDGET CONTROLLER code to the `src/extensions/`
  directory.
- Note that it is a requirement (enforced by register_binding_controller) that
  controller classes define a `model` trait which binds them to the scene MODEL
  class which they use. The unit tests will break if you forget this.
- Add unit tests for your controller. Look at tests for existing controllers if
  you are curious how that's accomplished.

UNIT TESTS
==========

- Add the UNIT TEST to the `src/extensions/tests/test_widget_**DISPLAYTYPE**.py`
  file


Connecting it all together
==========================

- add import of the MODEL to the `src/extensions/widget_**DISPLAYTYPE**.py` file
- Make sure the controller class is decorated with `register_binding_controller`
