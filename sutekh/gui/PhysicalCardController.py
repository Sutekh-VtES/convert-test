# PhysicalCardController.py
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sqlobject import SQLObjectNotFound
from sutekh.gui.PhysicalCardView import PhysicalCardView
from sutekh.gui.PhysicalCardMenu import PhysicalCardMenu
from sutekh.gui.DeleteCardDialog import DeleteCardDialog
from sutekh.core.SutekhObjects import PhysicalCard, AbstractCard, PhysicalCardSet

class PhysicalCardController(object):
    def __init__(self, oFrame, oConfig, oMainWindow):
        self.__oMainWin = oMainWindow
        self.__oFrame = oFrame
        self.__oView = PhysicalCardView(self, oMainWindow, oConfig)
        self._sFilterType = 'PhysicalCard'

    view = property(fget=lambda self: self.__oView, doc="Associated View")
    frame = property(fget=lambda self: self.__oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType, doc="Associated Type")

    def getView(self):
        return self.__oView

    def decCard(self, sName, sExpansion):
        """
        Returns True if a card was successfully removed, False otherwise.
        """
        print "decCard", sName, sExpansion
        return
        try:
            oC = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        # Go from Name to Abstract Card ID to Physical card ID
        # which is needed for delete
        # find Physical cards cards with this name
        cardCands = PhysicalCard.selectBy(abstractCardID=oC.id)

        # check we found something?
        if cardCands.count() == 0:
            return False

        # Loop throgh list and see if we can find a card
        # not present in any PCS
        dPCS = {}
        aPhysicalCardSets = PhysicalCardSet.select()
        for card in cardCands.reversed():
            idtodel = card.id
            dPCS[idtodel] = [0, []]
            for oPCS in aPhysicalCardSets:
                subset = [x for x in oPCS.cards if x.id == idtodel]
                if len(subset)>0:
                    dPCS[idtodel][0] += 1;
                    dPCS[idtodel][1].append(oPCS.name)
            if dPCS[idtodel][0] == 0:
                # OK, can delete this one and be done with it
                PhysicalCard.delete(idtodel)
                return True
        # All physical cards are assigned to PhysicalCardSets, so find the
        # one in the fewest
        T = min(dPCS.values())
        aList = [x for x in dPCS if T is dPCS[x]]
        idtodel = aList[-1]
        candtodel = dPCS[idtodel]
        # This is probably overcomplicated, need to revisit this sometime
        # Prompt the user for confirmation
        Dialog = DeleteCardDialog(self.__oWin, candtodel[1])
        Dialog.run()
        if Dialog.getResult():
            # User agrees
            # Delete card from all the PhysicalCardSets first
            for sPCS in candtodel[1]:
                oPC = PhysicalCardSet.byName(sPCS)
                oPC.removePhysicalCard(idtodel)
            PhysicalCard.delete(idtodel)
            # Reload everything
            self.__oC.getManager().reloadAllPhysicalCardSets()
            return True

    def incCard(self, sName, sExpansion):
        """
        Returns True if a card was successfully added, False otherwise.
        """
        return self.addCard(sName, sExpansion)

    def addCard(self, sName, sExpansion):
        """
        Returns True if a card was successfully added, False otherwise.
        """
        print "addCard", sName, sExpansion
        try:
            oC = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        if sExpansion is None:
            # Adding a new card to the list
            oPC = PhysicalCard(abstractCard=oC, expansion=None)
            self.view._oModel.incCardByName(oC.name)
            self.view._oModel.incCardExpansionByName(oC.name, sExpansion)
        return True

    def setCardText(self, sCardName):
        self.__oMainWin.set_card_text(sCardName)

