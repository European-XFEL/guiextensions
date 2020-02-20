.. _gui-extensions-developing:

********************
Developing the Scene
********************

As it is an important part of the Karabo GUI, we expect that the Scene will
require new widgets/elements and other changes as time goes by.
The karabo GUI scene code is generally split into two parts: model and view.
The original model code lives in ``karabo.common.scenemodel`` and is responsible for the
representation of scene data and reading/writing those data to/from files. It
is built using the `Traits library <http://docs.enthought.com/traits/>`_, which
you should familiarize yourself with if you plan to work on the scene. The view
code for the scene lives in ``karabogui.sceneview``. It is built using Qt and
makes use of the model objects.

.. note::

  This separation of model and view has an important benefit: You do not *need*
  a GUI to work with scenes. Having a well defined and **independent** data
  model means that power users can script the creation/modification of scene
  files.

Following the same principle, the ``GUI Extensions`` provide model/view based
code. Widgets can be wheeled in ``karabo GUI extension namespace`` and registered
in to the widget factory of the karabo GUI. The registration already uses the model
information provided. Reader and writer for the extension widgets must also be
created in this package.

The scene code is generally split into two parts: **model** and **view**.

Data Model
==========

Add a model to the Scene File format
------------------------------------

If you wish to add new data to the scene file format, or change the format of
data which is already there, you should take note of the following:

* If adding a new element, create a class which inherits ``BaseSceneObjectData``
  (a *model class*).

  * Create a reader function for the class. Register the reader with the
    ``register_scene_reader`` decorator.
  * Create a writer function for the class. Register the writer with the
    ``register_scene_writer`` decorator.
  * **Add unit tests which cover all the new code that you added**. Try to cover
    edge cases that you can think of.

* If *lightly* modifying an existing model class, you can make small changes to
  the reader function

  * **Leave the** ``SCENE_FILE_VERSION`` **constant alone**.
  * Make whatever changes are necessary to the model class.
  * Update the other reader function(s) for the model if needed
  * Update unit tests carefully.

* If modifying an existing model class in a way which requires a new reader
  function:

  * Increment the ``SCENE_FILE_VERSION`` constant first.
  * Make whatever changes are necessary to the model class.
  * Create a **new reader function** and register it with a version equal to the
    new value of ``SCENE_FILE_VERSION``. Remember not to use
    ``SCENE_FILE_VERSION`` here. Use its value.
  * Update the old reader function(s), **but only if NOT doing so would cause
    an exception when instantiating the model class**.

    * The overall aim is to construct the latest version of the model class from
      *any* version of the file data.

  * Update unit tests carefully.

.. note::

  Removing data from the file format is always safe. Old files which contain the
  data will continue to be readable, because the reader can simply ignore the
  data.

.. note::

  Similarly, adding new widgets to the file format is also safe, as long as the
  addition is orthogonal to existing data in the format.


Adding a View - WIDGET CONTROLLER
=================================

If you haven't added the data for your widget to the scene model yet, you
should first do that before proceeding with the view portion. Once your new
widget has a data model class associated with it, you can make it appear in the
scene by doing the following:

* Create a ``BaseBindingController`` class (or classes) which will be shown in
  the scene.
* Make sure your controller class has a ``model`` trait which is an ``Instance``
  of whatever your scene model class is.
* Register your controller class with the ``register_binding_controller``
  decorator.
* Add unit tests for your controller class.
* Test in the GUI.
