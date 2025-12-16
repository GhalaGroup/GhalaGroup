# -*- coding: utf-8 -*-
from . import controllers
from . import models


def _create_default_footers(env):
    """Create default footer configs for all companies that don't have them"""
    env['vpa.footer.config'].init_default_footers_all_companies()
