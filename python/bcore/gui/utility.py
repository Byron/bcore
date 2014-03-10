#-*-coding:utf-8-*-
"""
@package bcore.gui.utility
@brief Misc utilities for use with GUIs

@copyright 2013 Sebastian Thiel
"""
__all__ = ['remove_widget_children']


def remove_widget_children(widget, may_remove = lambda w: True):
    """Remove all of the widgets children from itself and from its layout if may_remove returns True"""
    layout = widget.layout()
    for child in widget.children():
        if not may_remove(child):
            continue
        # end keep layout
        layout.removeWidget(child)
        child.setParent(None)
    # end handle child removal
    
    while layout.count():
        layout.takeAt(0)
    # end take remaining
