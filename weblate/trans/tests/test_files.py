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
Tests for import and export.
"""

from __future__ import unicode_literals

from django.core.urlresolvers import reverse

from weblate.trans.tests.test_views import ViewTestCase
from weblate.trans.tests.utils import get_test_file

TEST_PO = get_test_file('cs.po')
TEST_CSV = get_test_file('cs.csv')
TEST_PO_BOM = get_test_file('cs-bom.po')
TEST_FUZZY_PO = get_test_file('cs-fuzzy.po')
TEST_MO = get_test_file('cs.mo')
TEST_ANDROID = get_test_file('strings-cs.xml')

TRANSLATION_OURS = 'Nazdar světe!\n'
TRANSLATION_PO = 'Ahoj světe!\n'


class ImportBaseTest(ViewTestCase):
    '''
    Base test of file imports.
    '''
    test_file = TEST_PO

    def setUp(self):
        super(ImportBaseTest, self).setUp()
        # We need extra privileges for overwriting
        self.user.is_superuser = True
        self.user.save()

    def do_import(self, **kwargs):
        '''
        Helper to perform file import.
        '''
        with open(self.test_file) as handle:
            params = {'file': handle}
            params.update(kwargs)
            return self.client.post(
                reverse(
                    'upload_translation',
                    kwargs=self.kw_translation
                ),
                params
            )


class ImportTest(ImportBaseTest):
    '''
    Testing of file imports.
    '''
    test_file = TEST_PO

    def test_import_normal(self):
        '''
        Test importing normally.
        '''
        response = self.do_import()
        self.assertRedirects(response, self.translation_url)

        # Verify stats
        translation = self.get_translation()
        self.assertEqual(translation.translated, 1)
        self.assertEqual(translation.fuzzy, 0)
        self.assertEqual(translation.total, 4)

        # Verify unit
        unit = self.get_unit()
        self.assertEqual(unit.target, TRANSLATION_PO)

    def test_import_header(self):
        '''
        Test importing with header merge.
        '''
        response = self.do_import(
            merge_header='1',
        )
        self.assertRedirects(response, self.translation_url)

        # Verify stats
        translation = self.get_translation()
        self.assertEqual(translation.translated, 1)
        self.assertEqual(translation.fuzzy, 0)
        self.assertEqual(translation.total, 4)

        # Verify unit
        unit = self.get_unit()
        self.assertEqual(unit.target, TRANSLATION_PO)

        # Verify header
        if self.test_file == TEST_PO:
            header = unit.translation.store.store.parseheader()
            self.assertEqual(
                header['Language-Team'], 'Test Team <noreply@weblate.org>'
            )
            self.assertIn(
                'Testing Weblate, 2015.',
                unit.translation.store.store.header().getnotes()
            )

    def test_import_author(self):
        '''
        Test importing normally.
        '''
        response = self.do_import(
            author_name='Testing User',
            author_email='noreply@weblate.org'
        )
        self.assertRedirects(response, self.translation_url)

        # Verify stats
        translation = self.get_translation()
        self.assertEqual(translation.translated, 1)
        self.assertEqual(translation.fuzzy, 0)
        self.assertEqual(translation.total, 4)

        # Verify unit
        unit = self.get_unit()
        self.assertEqual(unit.target, TRANSLATION_PO)

    def test_import_overwrite(self):
        '''
        Test importing with overwriting.
        '''
        # Translate one unit
        self.change_unit(TRANSLATION_OURS)

        response = self.do_import(overwrite='yes')
        self.assertRedirects(response, self.translation_url)

        # Verify unit
        unit = self.get_unit()
        self.assertEqual(unit.target, TRANSLATION_PO)

    def test_import_no_overwrite(self):
        '''
        Test importing without overwriting.
        '''
        # Translate one unit
        self.change_unit(TRANSLATION_OURS)

        response = self.do_import()
        self.assertRedirects(response, self.translation_url)

        # Verify unit
        unit = self.get_unit()
        self.assertEqual(unit.target, TRANSLATION_OURS)

    def test_import_fuzzy(self):
        '''
        Test importing as fuzzy.
        '''
        response = self.do_import(method='fuzzy')
        self.assertRedirects(response, self.translation_url)

        # Verify unit
        unit = self.get_unit()
        self.assertEqual(unit.target, TRANSLATION_PO)
        self.assertEqual(unit.fuzzy, True)

        # Verify stats
        translation = self.get_translation()
        self.assertEqual(translation.translated, 0)
        self.assertEqual(translation.fuzzy, 1)
        self.assertEqual(translation.total, 4)

    def test_import_suggest(self):
        '''
        Test importing as suggestion.
        '''
        response = self.do_import(method='suggest')
        self.assertRedirects(response, self.translation_url)

        # Verify unit
        unit = self.get_unit()
        self.assertEqual(unit.translated, False)

        # Verify stats
        translation = self.get_translation()
        self.assertEqual(translation.translated, 0)
        self.assertEqual(translation.fuzzy, 0)
        self.assertEqual(translation.total, 4)
        self.assertEqual(
            translation.have_suggestion,
            1
        )


class BOMImportTest(ImportTest):
    test_file = TEST_PO_BOM


class ImportFuzzyTest(ImportBaseTest):
    '''
    Testing of fuzzy file imports.
    '''
    test_file = TEST_FUZZY_PO

    def test_import_normal(self):
        '''
        Test importing normally.
        '''
        response = self.do_import(
            fuzzy=''
        )
        self.assertRedirects(response, self.translation_url)

        # Verify stats
        translation = self.get_translation()
        self.assertEqual(translation.translated, 0)
        self.assertEqual(translation.fuzzy, 0)
        self.assertEqual(translation.total, 4)

    def test_import_process(self):
        '''
        Test importing normally.
        '''
        response = self.do_import(
            fuzzy='process'
        )
        self.assertRedirects(response, self.translation_url)

        # Verify stats
        translation = self.get_translation()
        self.assertEqual(translation.translated, 0)
        self.assertEqual(translation.fuzzy, 1)
        self.assertEqual(translation.total, 4)

    def test_import_approve(self):
        '''
        Test importing normally.
        '''
        response = self.do_import(
            fuzzy='approve'
        )
        self.assertRedirects(response, self.translation_url)

        # Verify stats
        translation = self.get_translation()
        self.assertEqual(translation.translated, 1)
        self.assertEqual(translation.fuzzy, 0)
        self.assertEqual(translation.total, 4)


class ImportMoTest(ImportTest):
    '''
    Testing of mo file imports.
    '''
    test_file = TEST_MO


class ImportMoPoTest(ImportTest):
    '''
    Testing of mo file imports.
    '''
    test_file = TEST_MO

    def create_subproject(self):
        # Needs to create PO file to have language pack option
        return self.create_po()


class AndroidImportTest(ViewTestCase):
    def create_subproject(self):
        return self.create_android()

    def test_import(self):
        with open(TEST_ANDROID) as handle:
            self.client.post(
                reverse(
                    'upload_translation',
                    kwargs=self.kw_translation
                ),
                {'file': handle}
            )
        # Verify stats
        translation = self.get_translation()
        self.assertEqual(translation.translated, 2)
        self.assertEqual(translation.fuzzy, 0)
        self.assertEqual(translation.total, 4)


class CSVImportTest(ViewTestCase):
    def test_import(self):
        translation = self.get_translation()
        self.assertEqual(translation.translated, 0)
        self.assertEqual(translation.fuzzy, 0)
        with open(TEST_CSV) as handle:
            self.client.post(
                reverse(
                    'upload_translation',
                    kwargs=self.kw_translation
                ),
                {'file': handle}
            )
        # Verify stats
        translation = self.get_translation()
        self.assertEqual(translation.translated, 1)
        self.assertEqual(translation.fuzzy, 0)


class ExportTest(ViewTestCase):
    '''
    Testing of file export.
    '''
    def create_subproject(self):
        # Needs to create PO file to have language pack option
        return self.create_po()

    def setUp(self):
        super(ExportTest, self).setUp()
        # Add some content so that .mo files is non empty
        self.edit_unit(
            'Hello, world!\n',
            'Nazdar svete!\n'
        )

    def test_export(self):
        response = self.client.get(
            reverse(
                'download_translation',
                kwargs=self.kw_translation
            )
        )
        self.assertContains(response, 'Weblate Hello World 2012')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=test-test-cs.po'
        )

    def test_language_pack(self):
        response = self.client.get(
            reverse(
                'download_language_pack',
                kwargs=self.kw_translation
            )
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=cs.mo'
        )
