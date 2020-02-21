*****************
Extension Widgets
*****************

As it is an important part of the Karabo GUI to be of generic nature, the
``Karabo GUI Extensions`` will provide non-generic widgets. They are mostly
coupled to ``Node`` values that contain multiple properties and tailored for
devices.


IPM Quadrant Widget
===================

The ``IPM Quadrant Widget`` is tailored to provide the beam position on
a quadrant. The intensity can be used to visualize that there is no beam.
A red marker circle will visualize the beam position on the quadrant. Regarding
the position values, normalized (0 - 1) values are expected.
Please talk to controls development team if you want to have the intensity tailored.

.. figure:: images/ipm_quadrant.png
   :alt: ipm_quadrant.png
   :align: center

- DisplayType: **WidgetNode|IPM-Quadrant**
- The Node Schema MUST contain three (3) elements:
    * **posX** (Float/Double)
    * **posY** (Float/Double)
    * **intensity** (Float/Double)

.. note::

   The widget is available since GUI Extension version **0.1.0**


Scatter Position Widget
=======================

The ``Scatter Position Widget`` is tailored to provide the beam position with the
standard deviation of time.
A scatter plot is provided to provide the last updated `N` data points. The number
of data points `N` can be configured with the maximum number of 1000. The most recent
update is always shown with a ``red`` data point.
The standard deviation information from the device is used to provide an ellipse
around the scatter cloud.

.. figure:: images/scatter_position.png
   :alt: scatter_position.png
   :align: center

- DisplayType: **WidgetNode|ScatterPosition**
- The Node Schema MUST contain four (4) elements:
    * **posX** (Float/Double)
    * **posY** (Float/Double)
    * **xSD** (Float/Double)
    * **ySD** (Float/Double)

.. note::

   The widget is available since GUI Extension version **0.2.0**
   Known devices are: ``XGM`` and ``BeamPositionMonitor``
