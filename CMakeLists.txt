
python_project(
		NAME
			bcore
		VERSION
			0.2.0-devel
		AUTHORS
			"Sebastian Thiel <byronimo@gmail.com>"
		ROOT_PACKAGE
			bcore
			bqc
			btransaction
		SPHINX_CONFIG_IN
			DEFAULT
		PYSIDE_UI_FILES
		    bqc/gui/qc_check.ui
			bqc/gui/qc_group.ui
			bqc/gui/qc.ui
			bcore/processcontrol/gui/ui/package.ui
			bcore/processcontrol/gui/controller.ui
			bcore/processcontrol/gui/ui/viewer.ui
			bcore/tests/fixtures/gui/test_import.ui
		SDKS
			pyside 1.2.1
		DOXYFILE_IN
			DEFAULT
		DOXYGEN_SOURCE_FILES_EXCLUDE
			bcore/lib
		)
