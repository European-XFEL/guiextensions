*****************************
Installing the latest version
*****************************

You can install the latest version of GUI Extensions in one of the following ways.

From Source code
================

- `git clone https://git.xfel.eu/karaboDevices/guiextensions`
- activate the environment of the GUI
- `pip install -e guiextensions`

If you already have the repository cloned, then

- `git pull`
- `pip install -e .`


Using GUI
=========
- Open Karabo GUI
- Select ``Check for Updates`` from ``Help`` menu. This opens a dialog.
- Click the refresh button to get the latest version.
- Click the "Update" button.


From command line
=================
You can update GUI Extensions by using the ``karabo-update-extensions`` executable as

`karabo-update-extensions --latest`
