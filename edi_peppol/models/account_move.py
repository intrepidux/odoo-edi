import logging, traceback
from odoo import models, api, _, fields

from lxml import etree, objectify
from lxml.etree import Element, SubElement, QName, tostring

_logger = logging.getLogger(__name__)

"""
# TODO: Remove if this is crecrepid!
# XML namespace class
class NSMAPS:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"

    NSMAP={'cac':cac, 'cbc':cbc, 'ubl':empty}

    XNS={'cac':cac,
         'cbc':cbc,
         'ubl':empty}

    ns = {k:'{' + v + '}' for k,v in NSMAP.items()}
"""

class Account_Move(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "peppol.toinvoice", "peppol.toorder", "peppol.frominvoice"]
    _description = "Module that facilitates convertion of buissness messages from and to PEPPOL."

    # Button click function comming from Odoo.
    def to_peppol_button(self):
        return self.to_peppol()

    # Button click function comming from Odoo.
    def from_peppol_button(self):
        return self.from_peppol()

    # Converts a account.move to a PEPPOL file.
    # Currently can only handle invoices, but is inteded to handle
    #  all different kinds of messages that PEPPOL can encode.
    def to_peppol(self):
        tree = etree.ElementTree(self.create_invoice())

        tree.write('/usr/share/odoo-edi/edi_peppol/demo/output.xml',
                   xml_declaration=True,
                   encoding='UTF-8',
                   pretty_print=True)

    # Converts a account.move from a PEPPOL file.
    # Currently can only handle invoices, but is inteded to handle
    #  all different kinds of messages that PEPPOL can encode.
    def from_peppol(self):
        tree = self.parse_xml('/usr/share/odoo-edi/edi_peppol/demo/output.xml')

        if tree is None:
            return None

        temp = self.import_invoice(tree)

        # Debugg function
        self.compare_account_moves(115, self.id)

        return temp

    # This is a debugging functions, which is intended to compare
    #  a invoice that is made into a PEPPOL and then back again,
    #  in its before and after states
    def compare_account_moves(self, to_peppol_id, from_peppol_id):
      to_dict = self.extra_account_move_info(to_peppol_id)
      from_dict = self.extra_account_move_info(from_peppol_id)

      for n in to_dict:
        text = f"{n}" + ": " + f"{to_dict[n]}" + " =/= " + f"{from_dict[n]}"
        if to_dict[n] != from_dict[n]:
          _logger.error(text)
        #else:
        #  _logger.warning(text)
      #_logger.warning(to_dict)

    # Helper Function for debugging pruposes
    def extra_account_move_info(self, move_id):
      dict = {}
      move = self.env['account.move'].browse(move_id)
      for a in dir(move):
        if not callable(getattr(move,a)):
          if not a.startswith('__'):
            if not a == '<lambda>':
              dict.update({a: getattr(move, a)})
      return dict