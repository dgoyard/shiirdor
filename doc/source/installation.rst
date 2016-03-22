
.. _install_guid:

======================
Installing `SCHIIRDOR`
======================

This tutorial will walk you through the process of installing the SCHIIRDOR cube:

    * **schiirdor**: a cube that can only be instanciated
      if `cubicweb is installed <https://docs.cubicweb.org/admin/setup>`_.


.. _install_schiirdor:

Installing schiirdor
====================

Installing the current version
------------------------------

Install from *github*
~~~~~~~~~~~~~~~~~~~~~

**Clone the project**

::

    cd $CLONEDIR
    git clone https://github.com/neurospin/schiirdor.git

**Update your CW_CUBES_PATH**

::

    export CW_CUBES_PATH=$CLONE_DIR/schiirdor:$CW_CUBES_PATH

Make sure the cube is in CubicWeb's path
----------------------------------------

::

    cubicweb-ctl list

Create an instance of the cube
------------------------------

::

    cubicweb-ctl create schiirdor toy_instance

You can then run the instance in debug mode:

::

    cubicweb-ctl start -D toy_instance

The last line of the prompt will indicate which url the 
instance can be reached by:

::

(cubicweb.twisted) INFO: instance started on http://url:port/

Change configuration
--------------------

The configuration file is stored on your system:

::

    ... etc/cubicweb.d/toy_instance/all-in-one.conf
