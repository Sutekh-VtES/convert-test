# pyprotocols_interface.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based on custom.py from pylint, so the license is
# GPL v2 or later - see the COPYRIGHT file for deatils

"""Custom checker for pylint - Detect pyprotocols "advises" to mark interfaces
   as implemented"""

# Add this pylintrc using load-plugins
# The path to this file needs to be in PYTHONPATH as pylint must be able
# to import this

from pylint.interfaces import IASTNGChecker
from pylint.checkers import BaseChecker
from logilab import astng

class MyPyProtocolsChecker(BaseChecker):
    """Check for PyProtocols advises syntax

       This is a bit clumsy, as it does a fair amount of AST walking on
       all the classes encountered, and monkey-patches the AST pylint
       uses."""

    __implements__ = IASTNGChecker

    name = 'custom_pyprotocols_interface'
    # Since we just add addtional info to the AST, we have no messages
    options = ()
    # We're going to mess with the AST, so we need to run first
    priority = -1

    def __init__(self, oLinter=None):
        """Constructor"""
        super(MyPyProtocolsChecker, self).__init__(oLinter)
        self._dInterfaces = {}

    def open(self):
        """initialize visit variables"""
        self._dInterfaces = {}

    def find_poss_advise_call(self, oNode, aClasses):
        """Check to see if we have a 'advise' function call"""
        # Ugly check here
        for oSubNode in oNode.getChildNodes():
            if not isinstance(oSubNode, astng.Discard):
                continue
            for oPossAdvise in oSubNode.getChildNodes():
                if not isinstance(oPossAdvise, astng.CallFunc):
                    continue
                if self.check_poss_advise_call(oPossAdvise, aClasses):
                    return True
        return False

    def check_poss_advise_call(self, oNode, aClasses):
        """Check if a promising looking call matches pyprotocols"""
        bNamedAdvise = False
        bProvides = False
        for oInfoNode in oNode.getChildNodes():
            if isinstance(oInfoNode, astng.Name) and \
                    oInfoNode.name == 'advise':
                bNamedAdvise = True
            elif isinstance(oInfoNode, astng.Keyword):
                if oInfoNode.name == 'instancesProvide':
                    bProvides = True
                    if bNamedAdvise:
                        if not self.extract_classes(oInfoNode, aClasses):
                            bProvides = False
        return bNamedAdvise and bProvides

    def extract_classes(self, oNode, aClasses):
        """Extract the inferface provided from the keyword node"""
        for oSubNode in oNode.getChildNodes():
            if not isinstance(oSubNode, astng.List):
                return False
            for oName in oSubNode.getChildNodes():
                if oName.name in self._dInterfaces:
                    aClasses.append(self._dInterfaces[oName.name])
        return True

    def visit_class(self, oNode):
        """Check class"""
        if oNode.type == 'interface' and oNode.name != 'Interface':
            # Cache interfaces we encounter
            self._dInterfaces[oNode.name] = oNode
        for oSubNode in oNode.getChildNodes():
            if oSubNode.statement():
                aClasses = []
                if self.find_poss_advise_call(oSubNode, aClasses):
                    #print oNode, 'Interface implementation detected', aClasses
                    # MONKEY-PATCH alert
                    # pylint expects to read the interfaces implemented
                    # via this function. We don't construct the data
                    # the default function requires, since that involves
                    # much messing with the AST, so we just monkey patch.
                    # Given that the logilab.astng moknkey patches compiler.ast
                    # extensively, this isn't that bad an option
                    # pylint: disable-msg=C0322
                    # C0322: pylint get's this wrong
                    oNode.interfaces = lambda herited=True, \
                            handler_func=None: aClasses


def register(oLinter):
    """required method to auto register this checker"""
    oLinter.register_checker(MyPyProtocolsChecker(oLinter))
