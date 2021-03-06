# -*- coding: utf-8 -*-
#
# Copyright © 2012 - 2016 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <https://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Tests for automatic translation
"""

from django.core.urlresolvers import reverse

from weblate.trans.models import SubProject
from weblate.trans.tests.test_views import ViewTestCase


class AutoTranslationTest(ViewTestCase):
    def setUp(self):
        super(AutoTranslationTest, self).setUp()
        # Need extra power
        self.user.is_superuser = True
        self.user.save()
        self.subproject2 = SubProject.objects.create(
            name='Test 2',
            slug='test-2',
            project=self.project,
            repo=self.git_repo_path,
            push=self.git_repo_path,
            vcs='git',
            filemask='po/*.po',
            template='',
            file_format='po',
            new_base='',
            allow_translation_propagation=False,
        )

    def test_none(self):
        '''
        Tests for automatic translation with no content.
        '''
        url = reverse('auto_translation', kwargs=self.kw_translation)
        response = self.client.post(
            url
        )
        self.assertRedirects(response, self.translation_url)

    def test_different(self):
        '''
        Tests for automatic translation with different content.
        '''
        self.edit_unit(
            'Hello, world!\n',
            'Nazdar svete!\n'
        )
        params = {'project': 'test', 'lang': 'cs', 'subproject': 'test-2'}
        url = reverse('auto_translation', kwargs=params)
        response = self.client.post(url)
        self.assertRedirects(response, reverse('translation', kwargs=params))
        # Check we've translated something
        translation = self.subproject2.translation_set.get(language_code='cs')
        self.assertEqual(translation.translated, 1)
