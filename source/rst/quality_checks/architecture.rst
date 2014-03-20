.. _bcore_qc:
.. tags: quality checks

Quality Check Framework
#######################

The Quality Check Framework provides tools to ensure that data passes through departments and projects without obvious technical defects. At the same time it can help artists and TDs troubleshoot problems in their scenes.

The framework consists of three major parts, explained in detail below. These are the core quality check module, all the implemented quality checks themselves and the quality check GUI.

Core Quality Check Module
*************************

Implementing Quality Checks
***************************

Quality Check GUI
*****************
Each level of grouping of the quality check core module has its own class and ui resource which wraps it in GUI functionality. 

The main GUI instantiantes a quality check runner (using the Component Architecture :ref:`_bcore_ca_main`) and acts as its delegate. The quality check runner in turn uses the CA to load and instantiate all the services relevant to the current context. It then tells the UI to process these quality checks and create their UI elements.

For each category encountered during the processing a quality check group UI element is created, which groups together all the UI elements created for the quality checks themselves.

Since the quality check runner responsible for running the checks uses the GUI as a delegate and reports results to it, the flow between runner, main UI and actual quality checks is a bit roundabout. The runner runs the check, calls the appropriate function in its delegate (the main UI), which in turn must pass it down to the quality check UI (through the group UI).
