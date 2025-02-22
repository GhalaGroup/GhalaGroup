# Copyright © 2023 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html).

from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseUsersCommon
from .common import TestProductLabel


@tagged('post_install', '-at_install')
class TestAccessRights(BaseUsersCommon, TestProductLabel):

    def test_access_internal_user(self):
        """ Test internal user's access rights """
        PrintWizard = self.env['print.product.label'].with_user(self.user_internal)
        wizard_as_internal_user = PrintWizard.browse(self.print_wizard.id)

        # Internal user can use label templates
        wizard_as_internal_user.read()

        # Internal user can change label templates
        wizard_as_internal_user.write({'template_id': self.label_template_50x25.id})

        # Internal user can preview label templates
        wizard_as_internal_user.action_print()
