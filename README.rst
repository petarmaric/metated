IMPORTANT NOTICE
================

This project has been retired. Please contact its author if you wish to take
over its maintenance.

About
=====

metaTED is a tool that makes it easy to download all of the `TED talks`_. It
does so by creating over 1,000 `metalinks`_ of TED talks varying in both the
quality levels and possible talk groupings by directory. Features include:

* Creates talks with informative file names - i.e.
  ``Unconventional Explanations/Hans Rosling on HIV - New facts and stunning data visuals.mp4``
  instead of original ``HansRosling_2009_480.mp4``.

* Provides subtitles for talks in over 85 supported languages. New
  languages and translations are added daily through the
  `TED Open Translation Project`_, and you help out by
  `becoming a translator today`_.

* Tries hard to get all of the talks, or at least most of them - with a good
  reason if some have failed.

* More choice - creates one metalink per available quality level
  (currently low, standard and high).

* More choice - creates one metalink per available talk grouping, with all
  talks belonging to the same group placed inside a common directory. The
  possible talk groupings are extracted from talks metadata (currently
  filming year, publishing year, event name and author).

* Aggressive caching throughout the project, to avoid expensive network/CPU
  operations as much as possible. Proper cache invalidation included.

* High levels of fault tolerance.

* Simple, yet powerful homegrown web crawler.

* Flexible and extensible software design with changes in mind.

* Provides both the console script and a public API.

.. _becoming a translator today: http://www.ted.com/translate/forted
.. _metalinks: http://en.wikipedia.org/wiki/Metalink
.. _TED talks: http://www.ted.com/
.. _TED Open Translation Project: http://www.ted.com/pages/view/id/287

Downloading TED talks
=====================

If you just want to `download TED talks`_, you don't need to install this
package, or even Python. All you need to do is get a
`download client that supports the Metalink standard`_ and choose one of the
`daily updated metalinks`_.

.. _download TED talks: http://metated.petarmaric.com/
.. _download client that supports the Metalink standard:
        http://en.wikipedia.org/wiki/Metalink#Client_programs
.. _daily updated metalinks: http://metated.petarmaric.com/

Installing and running metaTED
==============================

You can install metaTED with `pip`_ via ``pip install metaTED``. You can run it
with ``metaTED``, or ``metaTED -h`` to get help and the list of all available
options.

The project itself is `hosted on GitHub`_, from where you can get the code
and report bugs.

.. _pip: http://pip.openplans.org/
.. _hosted on GitHub: https://github.com/petarmaric/metated
