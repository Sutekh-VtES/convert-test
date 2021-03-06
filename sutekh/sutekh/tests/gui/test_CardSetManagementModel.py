# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Card Set Management Model"""

from gi.repository import Gtk

from sutekh.tests.TestCore import SutekhTest
from sutekh.base.core.BaseTables import PhysicalCardSet
from sutekh.base.core import BaseFilters
from sutekh.base.gui.CardSetManagementModel import CardSetManagementModel


class DummyWindow:
    """Dummy main window object"""

    # pylint: disable=no-self-use
    # Must be a method to act as dummy
    def find_pane_by_name(self, sName):
        """Proxy for the find_pane_by_name method"""
        if sName == "Card Set 1":
            return True
        return False

    def find_cs_pane_by_set_name(self, sName):
        """Proxy for the find_cs_pane_by_Set_name method"""
        return self.find_pane_by_name(sName)


class CardSetManagementModelTests(SutekhTest):
    """Class for the test cases"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_basic(self):
        """Test the basic functionality"""
        # Create card sets
        oRoot = PhysicalCardSet(name='Root')
        PhysicalCardSet(name='Sib')
        oChild = PhysicalCardSet(name='Child', parent=oRoot)
        oChild2 = PhysicalCardSet(name='Child 2 Branch', parent=oRoot)
        for iCnt in range(4):
            PhysicalCardSet(name='Card Set %d' % iCnt, parent=oChild)
        for iCnt in range(2):
            PhysicalCardSet(name='Child 2 Card Set %d' % iCnt, parent=oChild2)
        oWin = DummyWindow()
        oModel = CardSetManagementModel(oWin)
        oModel.enable_sorting()
        oModel.load()

        self.assertEqual(oModel.get_card_set_iterator(None).count(), 10)
        # expected failure
        self.assertEqual(oModel.get_path_from_name('aaffr'), None)
        # Test model structure
        self.assertEqual(oModel.get_path_from_name('Root'), Gtk.TreePath("0"))
        self.assertEqual(oModel.get_path_from_name('Sib'), Gtk.TreePath("1"))
        self.assertEqual(oModel.get_path_from_name('Child'), Gtk.TreePath("0:0"))
        self.assertEqual(oModel.get_path_from_name('Child 2 Branch'), Gtk.TreePath("0:1"))
        self.assertEqual(oModel.get_path_from_name('Card Set 1'), Gtk.TreePath("0:0:1"))
        self.assertEqual(oModel.get_path_from_name('Card Set 3'), Gtk.TreePath("0:0:3"))
        self.assertEqual(oModel.get_path_from_name('Child 2 Card Set 0'),
                         Gtk.TreePath("0:1:0"))
        # Test filtering
        oFilter = BaseFilters.CardSetNameFilter('Child 2')
        self.assertEqual(oModel.get_card_set_iterator(oFilter).count(), 3)
        oModel.selectfilter = oFilter
        oModel.applyfilter = True
        oModel.load()
        # Test that tree is there, with parents retained
        self.assertEqual(oModel.get_path_from_name('Root'), Gtk.TreePath("0"))
        self.assertEqual(oModel.get_path_from_name('Sib'), None)
        self.assertEqual(oModel.get_path_from_name('Child 2 Branch'), Gtk.TreePath("0:0"))
        self.assertEqual(oModel.get_path_from_name('Child 2 Card Set 0'),
                         Gtk.TreePath("0:0:0"))
        oModel.applyfilter = False
        oModel.load()
        # Test that tree is restored
        self.assertEqual(oModel.get_path_from_name('Root'), Gtk.TreePath("0"))
        self.assertEqual(oModel.get_path_from_name('Sib'), Gtk.TreePath("1"))
        self.assertEqual(oModel.get_path_from_name('Child'), Gtk.TreePath("0:0"))
        self.assertEqual(oModel.get_path_from_name('Child 2 Branch'), Gtk.TreePath("0:1"))
        self.assertEqual(oModel.get_path_from_name('Card Set 1'), Gtk.TreePath("0:0:1"))

        oFilter = BaseFilters.CardSetNameFilter('Child 2 Branch')
        self.assertEqual(oModel.get_card_set_iterator(oFilter).count(), 1)
        oModel.selectfilter = oFilter
        oModel.applyfilter = True
        oModel.load()
        # test filter results
        self.assertEqual(oModel.get_path_from_name('Root'), Gtk.TreePath("0"))
        self.assertEqual(oModel.get_path_from_name('Sib'), None)
        self.assertEqual(oModel.get_path_from_name('Child 2 Branch'), Gtk.TreePath("0:0"))
        self.assertEqual(oModel.get_path_from_name('Child 2 Card Set 0'), None)
