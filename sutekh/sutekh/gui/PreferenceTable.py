# PreferenceTable.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Table widget for editing a list of options.
# Copyright 2010 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk


class PreferenceTable(gtk.Table):
    """A widget for editing a list of options."""
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods

    COLUMNS = 3
    KEY_COL, ENTRY_COL, INHERIT_COL = range(COLUMNS)

    def __init__(self, aOptions, oValidator):
        self._aOptions = []
        for sKey, sConfigSpec, bInherit in aOptions:
            self._aOptions.append(
                PreferenceOption(sKey, sConfigSpec, oValidator))

        super(PreferenceTable, self).__init__(
            rows=len(self._aOptions), columns=self.COLUMNS)
        self.set_col_spacings(5)
        self.set_row_spacings(5)

        dAttachOpts = {
            "xoptions": 0,
            "yoptions": 0,
        }
        for iRow, oOpt in enumerate(self._aOptions):
            self.attach(oOpt.oLabel, self.KEY_COL, self.KEY_COL+1,
                iRow, iRow+1, **dAttachOpts)
            self.attach(oOpt.oEntry, self.ENTRY_COL, self.ENTRY_COL+1,
                iRow, iRow+1, **dAttachOpts)
            self.attach(oOpt.oInherit, self.INHERIT_COL, self.INHERIT_COL+1,
                iRow, iRow+1, **dAttachOpts)

    def update_values(self, dNewValues, dInherit):
        """Update the option values.

           dNewValues is an sKey -> sValue mapping.
           dInherit is an sKey -> bInheritable mapping.
           """
        for oOpt in self._aOptions:
            oOpt.set_inheritable(dInherit.get(oOpt.sKey, True))
            oOpt.set_value(dNewValues.get(oOpt.sKey))

    def get_values(self):
        """Return a dictionary of option values."""
        return dict((oOpt.sKey, oOpt.get_value()) for oOpt in self._aOptions)


class PreferenceOption(object):
    """An option for a preference table."""

    def __init__(self, sKey, sConfigSpec, oValidator):
        self.sKey = sKey
        self.oSpec = parse_spec(sConfigSpec, oValidator)
        self.oEntry = self.oSpec.oEntry
        self.oLabel = gtk.Label(sKey.capitalize())
        self.bInheritable = True
        self.oInherit = gtk.CheckButton("use default")
        self.oInherit.connect("toggled", self._inherit_toggled)

    def set_inheritable(self, bInheritable):
        self.bInheritable = bInheritable
        if bInheritable:
            self.oInherit.set_sensitive(True)
            self.oInherit.show()
        else:
            self.oInherit.set_sensitive(False)
            self.oInherit.hide()

    def set_value(self, oValue):
        """Update the value of the option."""
        if oValue is None and self.bInheritable:
            self.oEntry.set_sensitive(False)
            self.oInherit.set_active(True)
        else:
            self.oEntry.set_sensitive(True)
            self.oInherit.set_active(False)
            self.oSpec.set_value(oValue)

    def get_value(self):
        """Return the value of the option."""
        if self.oInherit.get_active():
            return None
        else:
            return self.oSpec.get_value()

    def _inherit_toggled(self, _oWidget):
        """Update the state after the inherit widget is toggled."""
        if self.oInherit.get_active():
            self.oEntry.set_sensitive(False)
        else:
            self.oEntry.set_sensitive(True)


class BaseParsedSpec(object):
    """Object holding the result of parsing a ConfigSpec check."""

    def __init__(self, sType, aArgs, dKwargs, sDefault):
        self.sType, self.aArgs, self.dKwargs, self.sDefault = \
            sType, aArgs, dKwargs, sDefault
        self.oEntry = self.create_widget()

    def create_widget(self):
        """Return a widget for editing this config spec."""
        raise NotImplementedError

    def set_value(self, oValue):
        """Set an editing widget value."""
        raise NotImplementedError

    def get_value(self):
        """Get the value from an editing widget."""
        raise NotImplementedError


class UneditableSpec(BaseParsedSpec):

    def create_widget(self):
        self._oOrigValue = None
        return gtk.Label()

    def set_value(self, oValue):
        self._oOrigValue = oValue
        self.oEntry.set_text(str(oValue))

    def get_value(self):
        return self._oOrigValue


class StringParsedSpec(BaseParsedSpec):

    def create_widget(self):
        return gtk.Entry()

    def set_value(self, oValue):
        if oValue is None:
            oValue = ""
        self.oEntry.set_text(str(oValue))

    def get_value(self):
        return self.oEntry.get_text()


class BooleanParsedSpec(BaseParsedSpec):

    def create_widget(self):
        return gtk.CheckButton()

    def set_value(self, oValue):
        if oValue:
            self.oEntry.set_active(True)
        else:
            self.oEntry.set_active(False)

    def get_value(self):
        return self.oEntry.get_active()


class OptionParsedSpec(BaseParsedSpec):

    def create_widget(self):
        oCombo = gtk.combo_box_new_text()
        for sValue in self.aArgs:
            oCombo.append_text(sValue)
        return oCombo

    def set_value(self, oValue):
        try:
            iIndex = self.aArgs.index(oValue)
        except ValueError:
            iIndex = -1
        self.oEntry.set_active(iIndex)

    def get_value(self):
        iIndex = self.oEntry.get_active()
        if iIndex < 0 or iIndex >= len(self.aArgs):
            return None
        return self.aArgs[iIndex]


class IntegerParsedSpec(BaseParsedSpec):

    def create_widget(self):
        iMin = self.dKwargs.get("min", 0)
        iMax = self.dKwargs.get("max", 100)

        oAdj = gtk.Adjustment(iMin, iMin, iMax, 1.0, 5.0, 0.0)
        oSpin = gtk.SpinButton(oAdj, 0, 0)
        oSpin.set_numeric(True)
        return oSpin

    def set_value(self, oValue):
        try:
            oValue = int(oValue)
        except Exception:
            pass
        else:
            self.oEntry.set_value(oValue)

    def get_value(self):
        return self.oEntry.get_value_as_int()


SPEC_TYPE_MAP = {
    "string": StringParsedSpec,
    "boolean": BooleanParsedSpec,
    "option": OptionParsedSpec,
    "integer": IntegerParsedSpec,
}


def parse_spec(sConfigSpec, oValidator):
    """Parse a configobj spec into a parsed spec."""
    # TODO: is it okay to use an _ method from the validator?
    sType, aArgs, dKwargs, sDefault = \
        oValidator._parse_with_caching(sConfigSpec)
    cParsedSpec = SPEC_TYPE_MAP.get(sType, UneditableSpec)
    return cParsedSpec(sType, aArgs, dKwargs, sDefault)