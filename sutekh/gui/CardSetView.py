# CardSetView.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sutekh.gui.CardListView import EditableCardListView
from sutekh.gui.DeleteCardSetDialog import DeleteCardSetDialog
from sutekh.core.Filters import PhysicalCardSetFilter, AbstractCardSetFilter
from sutekh.core.SutekhObjects import PhysicalCard, PhysicalCardSet, AbstractCardSet, \
        MapAbstractCardToAbstractCardSet

class CardSetView(EditableCardListView):
    def __init__(self, oMainWindow, oController, sName, sSetType, oConfig):
        super(CardSetView,self).__init__(oController, oMainWindow, oConfig)
        self.sSetName = sName
        self.sSetType = sSetType
        if sSetType == "Physical Card Set":
            # cardclass is the actual physicalcard
            self._oModel.cardclass = PhysicalCard
            self._oModel.basefilter = PhysicalCardSetFilter(self.sSetName)
        elif sSetType == "Abstract Card Set":
            # Need MapAbstractCardToAbstractCardSet here, so filters do the right hing
            self._oModel.cardclass = MapAbstractCardToAbstractCardSet
            self._oModel.basefilter = AbstractCardSetFilter(self.sSetName)
        else:
            # Should this be an error condition?
            self._oModel.basefilter = None

        self.load()

    def dragCard(self, btn, context, selection_data, info, time):
        if self._oSelection.count_selected_rows()<1:
            return
        oModel, oPathList = self._oSelection.get_selected_rows()
        selectData = "CardSet:"+self.sSetType+":"+self.sSetName
        for oPath in oPathList:
            oIter = oModel.get_iter(oPath)
            sCardName = oModel.get_value(oIter,0)
            number = str(oModel.get_value(oIter,1))
            selectData = selectData + "\n" + number + "_" + sCardName
        selection_data.set(selection_data.target, 8, selectData)

    def cardDrop(self, w, context, x, y, data, info, time):
        lines = data.data.splitlines()
        # We need to do things in this order as cardNames can include :
        bits = lines[0].split(":")
        if data and data.format == 8 and bits[0] == "Phys":
            # Card is from the Physical card view, so we only get one
            for name in lines[1:]:
                self.addCard(name)
            context.finish(True, False, time)
        elif data and data.format == 8 and bits[0] == "Abst" \
                and self.sSetType == "Abstract Card Set":
            # Abstract Card Sets can accept cards from the Abstract Card List
            # Card is from the Abstract card view, so we only get one
            for name in lines[1:]:
                self.addCard(name)
            context.finish(True, False, time)
        elif data and data.format == 8 and bits[0] == "CardSet":
            # Card is from a CardSet, so extract type and name
            sourceType = bits[1]
            sourceSetName = bits[2]
            if sourceSetName != self.sSetName or sourceType != self.sSetType:
                # different Set, so try and add number cards
                # We rely on addCard to prevent stuff becoming
                # inconsistent
                for candidate in lines[1:]:
                    [number, name] = candidate.split('_')
                    for j in range(int(number)):
                        self.addCard(name)
            context.finish(True,False, time)
        else:
            context.finish(False, False, time)

    def deleteCardSet(self):
        # Check if CardSet is empty
        if self.sSetType == "Physical Card Set":
            oCS = PhysicalCardSet.byName(self.sSetName)
        else:
            oCS = AbstractCardSet.byName(self.sSetName)
        if len(oCS.cards)>0:
            # Not empty, ask user if we should delete it
            Dialog = DeleteCardSetDialog(self._oWin,self.sSetName,self.sSetType)
            Dialog.run()
            if not Dialog.getResult():
                return False # not deleting

            # User agreed, so clear the CardSet
            if self.sSetType == "Physical Card Set":
                for oC in oCS.cards:
                    oCS.removePhysicalCard(oC)
            else:
                for oC in oCS.cards:
                    oCS.removeAbstractCard(oC)

        # Card Set now empty
        if self.sSetType == "Physical Card Set":
            cardSet = PhysicalCardSet.byName(self.sSetName)
            PhysicalCardSet.delete(cardSet.id)
        else:
            cardSet = AbstractCardSet.byName(self.sSetName)
            AbstractCardSet.delete(cardSet.id)
        # Tell Window to clean up
        return True
