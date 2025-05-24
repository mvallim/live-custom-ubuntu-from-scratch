# -*- coding: utf-8; Mode: Python; indent-tabs-mode: nil; tab-width: 4 -*-
#
# Copyright (C) 2013 Canonical Ltd.
#
# Author:
#   Aurélien Gâteau <agateau@kde.org>
#
# This file is part of Ubiquity.
#
# Ubiquity is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or at your option)
# any later version.
#
# Ubiquity is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with Ubiquity; if not, write to the Free Software Foundation, Inc., 51
# Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
from string import Template

UIDIR = "/usr/share/ubiquity/qt"


def load(filename, ltr):
    with open(os.path.join(UIDIR, filename)) as style:
        tmpl = Template(style.read())
    args = {}
    if ltr:
        args["direction"] = "_ltr"
    else:
        args["direction"] = "_rtl"
    return tmpl.substitute(args)
