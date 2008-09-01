# test_CardSetUtilities.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test cases for the CardSetUtilities functions"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.core.CardSetUtilities import delete_physical_card_set, \
        get_loop_names, detect_loop, find_children
import unittest

class CardSetUtilTests(SutekhTest):
    """class for the Card Set Utility tests"""

    def test_basic(self):
        """Test behaviour without loops"""
        oRoot = PhysicalCardSet(name='Root')
        oChild = PhysicalCardSet(name='Child', parent=oRoot)
        aChildren = []
        for iCnt in range(4):
            oSet = PhysicalCardSet(name='Card Set %d' % iCnt, parent=oChild)
            aChildren.append(oSet)
        # Check detect_loop fails
        self.assertFalse(detect_loop(oRoot))
        self.assertFalse(detect_loop(oChild))

        # Check find_children behaves properly
        aFoundChildren = find_children(oRoot)
        self.assertEqual(len(aFoundChildren), 1)
        self.assertEqual(aFoundChildren[0].name, oChild.name)
        aFoundChildren = find_children(oChild)
        self.assertEqual(len(aFoundChildren), 4)
        self.assertEqual(sorted([x.name for x in aFoundChildren]),
                sorted([x.name for x in aChildren]))

        # Check children are reparented correctly
        delete_physical_card_set(oChild.name)
        aFoundChildren = find_children(oRoot)
        self.assertEqual(len(aFoundChildren), 4)
        self.assertEqual(sorted([x.name for x in aFoundChildren]),
                sorted([x.name for x in aChildren]))

        # Check ordinary deletion
        delete_physical_card_set(aChildren[0].name)
        aFoundChildren = find_children(oRoot)
        self.assertEqual(len(aFoundChildren), 3)
        self.assertEqual(sorted([x.name for x in aFoundChildren]),
                sorted([x.name for x in aChildren[1:]]))

    def test_loops(self):
        """Test loop detection and loop handling"""
        # Create a loop
        oRoot = PhysicalCardSet(name='Root')
        oChild = PhysicalCardSet(name='Child', parent=oRoot)
        aChildren = []
        for iCnt in range(4):
            oSet = PhysicalCardSet(name='Card Set %d' % iCnt, parent=oChild)
            aChildren.append(oSet)
        oRoot.parent = aChildren[0]
        oRoot.syncUpdate()

        # Check that detect_loop picks this up
        self.assertTrue(detect_loop(oRoot))
        self.assertTrue(detect_loop(oChild))
        self.assertTrue(detect_loop(aChildren[0]))
        # This will also run round the loop
        self.assertTrue(detect_loop(aChildren[1]))

        # Check we identify the right cards in the loop
        aList1 = get_loop_names(oRoot)
        self.assertEqual(aList1, ['Child', 'Card Set 0', 'Root'])
        aList2 = get_loop_names(oChild)
        self.assertEqual(sorted(aList2), sorted(aList1))
        aList3 = get_loop_names(aChildren[1])
        self.assertEqual(sorted(aList3), sorted(aList1))
        # Check that deleting doesn't fix the loop, due to reparenting
        delete_physical_card_set(aChildren[0].name)
        self.assertTrue(detect_loop(oRoot))
        # Check that explicit loop breaking working
        oRoot.parent = None
        oRoot.syncUpdate()
        self.assertFalse(detect_loop(oRoot))
        self.assertFalse(detect_loop(aChildren[1]))
        aList1 = get_loop_names(oRoot)
        self.assertEqual(len(aList1), 0)


if __name__ == "__main__":
    unittest.main()