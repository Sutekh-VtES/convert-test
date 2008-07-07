# test_CardSetListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Card List Model"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.gui.CardListModel import CardListModelListener
from sutekh.gui.CardSetListModel import CardSetCardListModel, \
        NO_SECOND_LEVEL, SHOW_EXPANSIONS, SHOW_CARD_SETS, \
        EXPANSIONS_AND_CARD_SETS, CARD_SETS_AND_EXPANSIONS, \
        THIS_SET_ONLY, ALL_CARDS, PARENT_CARDS, CHILD_CARDS, \
        IGNORE_PARENT, PARENT_COUNT, MINUS_THIS_SET, MINUS_SETS_IN_USE
from sutekh.core.Groupings import NullGrouping
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCard, \
        IExpansion, IAbstractCard, MapPhysicalCardToPhysicalCardSet
import unittest

class CardSetListener(CardListModelListener):
    """Listener used in the test cases."""
    # pylint: disable-msg=W0231
    # CardListModelListener has no __init__
    def __init__(self):
        self.bLoadCalled = False
        self.aCards = []

    def load(self, aAbsCards):
        """Called when the model is loaded."""
        self.bLoadCalled = True
        self.aCards = aAbsCards

class CardSetListModelTests(SutekhTest):
    """Class for the test cases"""

    # pylint: disable-msg=R0201
    # I prefer to have these as methods
    def _count_second_level(self, oModel):
        """Count all the second level entries in the model."""
        iTotal = 0
        oIter = oModel.get_iter_first()
        # We assume grouping is NullGrouping here
        oChildIter = oModel.iter_children(oIter)
        while oChildIter:
            iTotal += oModel.iter_n_children(oChildIter)
            oChildIter = oModel.iter_next(oChildIter)
        return iTotal

    def _count_all_cards(self, oModel):
        """Count all the entries in the model."""
        iTotal = 0
        # We assume grouping is NullGrouping here
        oIter = oModel.get_iter_first()
        iTotal = oModel.iter_n_children(oIter)
        return iTotal

    def _get_all_child_counts(self, oModel, oIter):
        """Recursively descend the children of oIter, getting all the
           relevant info."""
        aList = []
        oChildIter = oModel.iter_children(oIter)
        while oChildIter:
            aList.append((oModel.get_card_count_from_iter(oChildIter),
                oModel.get_parent_count_from_iter(oChildIter),
                oModel.get_name_from_iter(oChildIter)))
            if oModel.iter_n_children(oChildIter) > 0:
                aList.extend(self._get_all_child_counts(oModel, oChildIter))
            oChildIter = oModel.iter_next(oChildIter)
        aList.sort()
        return aList

    def _get_all_counts(self, oModel):
        """Return a list of iCnt, iParCnt, sCardName tuples from the Model"""
        return self._get_all_child_counts(oModel, None)

    def _gen_card(self, sName, sExp):
        """Create a card given the name and Expansion"""
        if sExp:
            oExp = IExpansion(sExp)
        else:
            oExp = None
        oAbs = IAbstractCard(sName)
        return IPhysicalCard((oAbs, oExp))

    def _format_error(self, sErrType, oTest1, oTest2, oModel):
        """Format an informative error message"""
        sModel = "Model (for card set %s) State : (ExtraLevelsMode : %d," \
                " ParentCountMode %d, ShowCardMode : %d, Editable: %s)" % (
                        oModel._oCardSet.name, oModel.iExtraLevelsMode,
                        oModel.iParentCountMode, oModel.iShowCardMode,
                        oModel.bEditable)
        return "%s : %s vs %s - %s" % (sErrType, oTest1, oTest2, sModel)

    # pylint: enable-msg=R0201

    def _add_remove_distinct_cards(self, oPCS, oModel):
        """Helper function to add and remove distinct cards from the card set,
           validating that the model works correctly"""
        aCards = [('AK-47', None), ('Bronwen', 'SW'), ('Cesewayo', None),
                ('Anna "Dictatrix11" Suljic', 'NoR'), ('Ablative Skin',
                    'Sabbat')]
        aPhysCards = []
        for sName, sExp in aCards:
            oCard = self._gen_card(sName, sExp)
            aPhysCards.append(oCard)
        # pylint: disable-msg=E1101
        # SQLObjext confuses pylint
        oModel.load()
        iStart = self._count_all_cards(oModel)
        for oCard in aPhysCards:
            oPCS.addPhysicalCard(oCard.id)
            oPCS.syncUpdate()
            oModel.inc_card(oCard)
        tAlterTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList1 = self._get_all_counts(oModel)
        oModel.load()
        tTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList2 = self._get_all_counts(oModel)
        self.assertEqual(tAlterTotals, tTotals, self._format_error(
            "Totals for inc_card and load differ", tAlterTotals, tTotals,
            oModel))
        self.assertEqual(aList1, aList2, self._format_error(
            "Card Lists for inc_card and load differ", aList1, aList2,
            oModel))
        # Card removal
        for oCard in aPhysCards:
            oPCS.removePhysicalCard(oCard.id)
            oPCS.syncUpdate()
            oModel.dec_card(oCard)
        tAlterTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList1 = self._get_all_counts(oModel)
        oModel.load()
        tTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList2 = self._get_all_counts(oModel)
        self.assertEqual(tAlterTotals, tTotals, self._format_error(
            "Totals for dec_card and load differ", tAlterTotals, tTotals,
            oModel))
        self.assertEqual(aList1, aList2, self._format_error(
            "Card lists for dec_card and load differ", aList1, aList2, oModel))
        # Also test that we've behaved sanely
        iEnd = self._count_all_cards(oModel)
        self.assertEqual(iEnd, iStart, self._format_error(
            "Card set differs from start after removals", iEnd, iStart,
            oModel))

    def _add_remove_repeated_cards(self, oPCS, oModel):
        """Helper function to add and remove repeated cards from the card set,
           validating that the model works correctly"""
        aCards = [('Alexandra', 'CE'), ('Alexandra', None),
                ('Ablative Skin', None)] * 5
        aPhysCards = []
        for sName, sExp in aCards:
            oCard = self._gen_card(sName, sExp)
            aPhysCards.append(oCard)
        oModel.load()
        iStart = self._count_all_cards(oModel)
        for oCard in aPhysCards:
            oPCS.addPhysicalCard(oCard.id)
            oPCS.syncUpdate()
            oModel.inc_card(oCard)
        tAlterTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList1 = self._get_all_counts(oModel)
        oModel.load()
        aList2 = self._get_all_counts(oModel)
        tTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        self.assertEqual(tAlterTotals, tTotals, self._format_error(
            "Totals for repeated inc_card and load differ", tAlterTotals,
            tTotals, oModel))
        self.assertEqual(aList1, aList2, self._format_error(
            "Card lists for repeated inc_card and load differ, ", aList1,
            aList2, oModel))
        # We use the map table, so we can also test dec_card properly
        for oCard in aPhysCards:
            oMapEntry = list(MapPhysicalCardToPhysicalCardSet.selectBy(
                    physicalCardID=oCard.id, physicalCardSetID=oPCS.id))[-1]
            MapPhysicalCardToPhysicalCardSet.delete(oMapEntry.id)
            oPCS.syncUpdate()
            oModel.dec_card(oCard)
        tAlterTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList1 = self._get_all_counts(oModel)
        oModel.load()
        aList2 = self._get_all_counts(oModel)
        tTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        self.assertEqual(tAlterTotals, tTotals, self._format_error(
            "Totals for repeated dec_card and load differ", tAlterTotals,
            tTotals, oModel))
        self.assertEqual(aList1, aList2, self._format_error(
            "Card lists for repeated dec_card and load differ, ", aList1,
            aList2, oModel))
        # sanity checks
        iEnd = self._count_all_cards(oModel)
        self.assertEqual(iEnd, iStart, self._format_error(
            "Card set differs from start after removals", iEnd, iStart,
            oModel))

    def _loop_modes(self, oPCS, oModel):
        """Loop over all the possible modes of the model, calling
           _add_remove_cards to test the model."""
        for bEditFlag in [False, True]:
            oModel.bEditable = bEditFlag
            for iLevelMode in [NO_SECOND_LEVEL, SHOW_EXPANSIONS,
                    SHOW_CARD_SETS, EXPANSIONS_AND_CARD_SETS,
                    CARD_SETS_AND_EXPANSIONS]:
                oModel.iExtraLevelsMode = iLevelMode
                for iParentMode in [IGNORE_PARENT, PARENT_COUNT,
                        MINUS_THIS_SET, MINUS_SETS_IN_USE]:
                    oModel.iParentCountMode = iParentMode
                    for iShowMode in [THIS_SET_ONLY, ALL_CARDS, PARENT_CARDS,
                            CHILD_CARDS]:
                        oModel.iShowCardMode = iShowMode
                        self._add_remove_distinct_cards(oPCS, oModel)
                        self._add_remove_repeated_cards(oPCS, oModel)

    def test_basic(self):
        """Set of simple tests of the Card Set List Model"""
        # pylint: disable-msg=R0915, R0914
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables

        sName = 'Test 1'
        oPCS = PhysicalCardSet(name=sName)
        oModel = CardSetCardListModel(sName)
        oListener = CardSetListener()
        oModel.load()
        self.assertFalse(oListener.bLoadCalled)
        oModel.add_listener(oListener)
        oModel.load()
        self.assertTrue(oListener.bLoadCalled)
        self.assertEquals(len(oListener.aCards), 0)
        # Check for the 'No cards' entry in the model
        self.assertEquals(oModel.iter_n_children(None), 1)
        aCards = [('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition')]
        for sName, sExp in aCards:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oPCS.addPhysicalCard(oCard.id)
        oModel.load()
        self.assertEqual(len(oListener.aCards), 2)
        # Only Vampires added
        self.assertEqual(oModel.iter_n_children(None), 1)
        oModel.groupby = NullGrouping
        self.assertEqual(self._count_all_cards(oModel), 2)
        self.assertEqual(self._count_second_level(oModel), 2)
        # Check the drag-n-drop helper
        self.assertEqual(oModel.get_drag_child_info('0'), {})
        self.assertEqual(oModel.get_drag_child_info('0:0:0'), {})
        self.assertEqual(oModel.get_drag_child_info('0:0'),
                {'Camarilla Edition' : 1})
        self.assertEqual(oModel.get_drag_info_from_path('0:0:0'),
                (u"Alexandra", "Camarilla Edition", 1, 2))
        self.assertEqual(oModel.get_drag_info_from_path('0:0'),
                (u"Alexandra", None, 1, 1))
        self.assertEqual(oModel.get_drag_info_from_path('0'),
                (None, None, 2, 0))
        oModel.iExtraLevelsMode = NO_SECOND_LEVEL
        oModel.load()
        # This should also work for no expansions shown
        self.assertEqual(self._count_all_cards(oModel), 2)
        self.assertEqual(self._count_second_level(oModel), 0)
        self.assertEqual(oModel.get_drag_child_info('0'), {})
        self.assertEqual(oModel.get_drag_child_info('0:0'),
                {'Camarilla Edition' : 1})
        # Add Cards
        self._loop_modes(oPCS, oModel)
        # Add some more cards
        aCards = [('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
                ('Alexandra', None), ('Bronwen', 'Sabbat'),
                ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
                ('Yvette, The Hopeless', 'CE'),
                ('Yvette, The Hopeless', 'BSC')]
        for sName, sExp in aCards:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oPCS.addPhysicalCard(oCard.id)
        # Create a child card set with some entries and check everything works
        sName2 = 'Test Child 1'
        oChildPCS = PhysicalCardSet(name=sName2, parent=oPCS)
        oChildModel = CardSetCardListModel(sName2)
        for sName, sExp in aCards[2:6]:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oChildPCS.addPhysicalCard(oCard.id)
        oChildModel.groupby = NullGrouping
        oChildModel.load()
        oChildPCS.inuse = False
        # Check adding cards when we have a parent card set
        self._loop_modes(oChildPCS, oChildModel)
        # Check adding cards when we have a child, ut no parent
        self._loop_modes(oPCS, oModel)
        # And when we're in use
        oChildPCS.inuse = True
        self._loop_modes(oChildPCS, oChildModel)
        self._loop_modes(oPCS, oModel)
        # Add a grand child
        sName3 = 'Test Grand Child'
        oChild2PCS = PhysicalCardSet(name=sName3, parent=oChildPCS)
        for sName, sExp in aCards[3:7]:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oChild2PCS.addPhysicalCard(oCard.id)
        oChild2PCS.inuse = False
        # Check adding cards when we have a parent card set and a child
        self._loop_modes(oChildPCS, oChildModel)
        oChild2PCS.inuse = True
        self._loop_modes(oChildPCS, oChildModel)
        # FIXME: Test the rest of the functionality
        # Test addition + deletion with parent card set, sibling card set
        # and child card sets
        # Test adding cards + removing card from parent card sets, child
        # card sets and siblings
        # Test filtering with the different modes

if __name__ == "__main__":
    unittest.main()
