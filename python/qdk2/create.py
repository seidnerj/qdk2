#!/usr/bin/env python

from argparse import SUPPRESS
from os.path import (exists as pexists,
                     join as pjoin,
                     dirname as pdirname,
                     basename as pbasename,
                     realpath as prealpath,
                     isdir,
                     )
from os import makedirs, listdir
from shutil import copytree, copy, rmtree, move
from basecommand import BaseCommand
from glob import glob
import fileinput


from settings import Settings
from exception import (BaseStringException,
                       UserExit,
                       )
from log import info, warning, error


class CommandCreate(BaseCommand):
    key = 'create'
    help = 'create a new QPKG from the template'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help=cls.help)
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('-p', '--project', metavar='NAME',
                            default=Settings.DEFAULT_PROJECT,
                            help='project name (default: %(default)s)')
        parser.add_argument('-d', '--directory', metavar='PATH',
                            default='./',
                            help='destination folder (default: %(default)s)')
        parser.add_argument('-t', '--template', metavar='TYPE',
                            choices=Settings.SUPPORT_TEMPLATES,
                            default=None,
                            help='create new QPKG from existed template')
        group = parser.add_argument_group('package format')
        mgroup = group.add_mutually_exclusive_group()
        mgroup.add_argument('--format-qdk1', action='store_true',
                            default=False,
                            help='QDK1 format (legacy)')
        mgroup.add_argument('--format-qdk2', action='store_true',
                            default=True,
                            help='QDK2 format (default)')

    def format_qdk1(self):
        info('The template are putting to ' + self.directory)
        if pexists(self.directory):
            yn = raw_input('{} folder exists! Confirm? [Y/n] '.format(
                           self.directory))
            if len(yn) and yn[0].lower() == 'n':
                raise UserExit()
        else:
            makedirs(self.directory)
        for fn in glob(pjoin(Settings.TEMPLATE_V1_PATH, '*')):
            dest = pjoin(self.directory, pbasename(fn))
            if isdir(fn):
                copytree(fn, dest, True)
            else:
                copy(fn, dest)

    def format_qdk2(self):
        info('Create CONTROL at {}'.format(self.directory))
        if pexists(pjoin(self.directory, Settings.CONTROL_PATH)):
            yn = raw_input('{} folder exists! Delete? [Y/n] '.format(
                           pjoin(self.directory, Settings.CONTROL_PATH)))
            if len(yn) and yn[0].lower() == 'n':
                raise UserExit()
            rmtree(pjoin(self.directory, Settings.CONTROL_PATH))
        if not pexists(self.directory):
            makedirs(self.directory)

        # copy template control files
        info('Copy default CONTROL files to {}'.format(
            pjoin(self.directory, Settings.CONTROL_PATH)))
        copytree(pjoin(Settings.TEMPLATE_PATH, Settings.CONTROL_PATH),
                 pjoin(self.directory, Settings.CONTROL_PATH), True)

        self.rename_ctrl_files()

    def copy_sample(self):
        if pexists(self.directory):
            if isdir(self.directory):
                if listdir(self.directory):
                    error('Directory is not empty: ' + self.directory)
                    return -1
            else:
                error('This is not directory: ' + self.directory)
                return -1

        # copy template data files
        if self.template in Settings.SUPPORT_TEMPLATES:
            info('Copy template data files: ' + self.template)
            copytree(pjoin(Settings.TEMPLATE_PATH, self.template),
                     self.directory, True)
        return 0

    def rename_ctrl_files(self):
        # rename
        if self._args.project != Settings.DEFAULT_PACKAGE:
            info('Modify package name to ' + self._args.project)
            # sed control, rules, *.init, *.conf
            files_check = ('control', 'rules', 'foobar.init', 'foobar.conf')
            for fn in files_check:
                fp = pjoin(self.directory, Settings.CONTROL_PATH, fn)
                for line in fileinput.input(fp, inplace=True):
                    print (line.replace(Settings.DEFAULT_PACKAGE,
                                       self._args.project)),

            # mv foobar.* to self._args.project.*
            for fn in glob(pjoin(self.directory, Settings.CONTROL_PATH,
                                 Settings.DEFAULT_PACKAGE + '.*')):
                dest = pjoin(pdirname(fn),
                             self._args.project + fn[fn.index('.'):])
                move(fn, dest)

    def run(self):
        if self.copy_sample() != 0:
            warning("Skip copy sample: " + self.template)

        try:
            if self._args.format_qdk1:
                info('Build QPKG with QDK1 format')
                self.format_qdk1()
            if self._args.format_qdk2:
                info('Build QPKG with QDK2 format')
                self.format_qdk2()
        except UserExit:
            pass
        except BaseStringException as e:
            error(str(e))
            return -1
        return 0

    @property
    def directory(self):
        if not hasattr(self, '_directory'):
            self._directory = pjoin(prealpath(self._args.directory),
                                    self._args.project)
        return self._directory

    @property
    def template(self):
        if not hasattr(self, '_template'):
            self._template = '' if self._args.template is None \
                else self._args.template
        return self._template


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
