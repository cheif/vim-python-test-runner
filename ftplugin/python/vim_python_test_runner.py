#!/bin/env python
import re
import os
import coverage
from xml.etree import ElementTree
DJANGO_COVERAGE_COMMAND = \
    'bump /opt/memoto/env/bin/coverage run -a manage.py test'


class TestCase(object):
    is_django = False

    def __init__(self, vim):
        self.vim = vim
        self.buffer = vim.current.buffer
        self.current_line = vim.current.window.cursor[0]
        full_path = self.buffer.name

        # Nose project?
        self.project_dir = self.find_dir_with(full_path, 'setup.py')
        if self.project_dir:
            self.test_cmd = "nosetests"
        else:
            # Django project?
            self.project_dir = self.find_dir_with(full_path, 'manage.py')
            if self.project_dir:
                self.is_django = True
                self.test_cmd = "bump django test"
            else:
                print "Couldn't determine type"
                return None

        root_relative_path = full_path.split(self.project_dir)[-1][1:]
        without_ext = os.path.splitext(root_relative_path)[0]
        self.basename = without_ext.replace('/', '.')

        # Should we save coverage?
        if self.is_django and self.vim.eval('g:test_runner_append_coverage'):
            self.test_cmd = DJANGO_COVERAGE_COMMAND.format(self.app)

    def find_dir_with(self, path, filename):
        """Find the directory containing setup.py"""
        path = os.path.dirname(path)

        while path != '/':
            if filename in os.listdir(path):
                return path
            path, curr = os.path.split(path)

    @property
    def app(self):
        if self.is_django:
            return ".".join(self.basename.split('.')[:2])
        else:
            return ''

    @property
    def filename(self):
        if self.is_django:
            return '.tests' + self.basename.split('tests')[1]
        else:
            return self.basename

    @property
    def cls(self):
        class_regex = re.compile(r"^class (?P<class_name>.+)\(")
        for line in xrange(self.current_line - 1, -1, -1):
            if class_regex.search(self.buffer[line]) is not None:
                class_name = class_regex.search(self.buffer[line])
                return class_name.group(1)

    @property
    def method(self):
        class_regex = re.compile(r"^class (?P<class_name>.+)\(")
        method_regex = re.compile(r"def (?P<method_name>.+)\(")
        for line in xrange(self.current_line - 1, -1, -1):
            if class_regex.search(self.buffer[line]) is not None:
                return None
            if method_regex.search(self.buffer[line]) is not None:
                method_name = method_regex.search(self.buffer[line])
                return method_name.group(1)

    def get_command(self, abbr):
        if abbr != 'rerun':
            command = self._get_command(abbr)
            self.vim.command("let g:last_test_command='{}'".format(command))
        return self.vim.eval('g:last_test_command')

    def _get_command(self, abbr):
        cmd = self.test_cmd
        if abbr != 'project':
            cmd += ' ' + self.app
            if abbr != 'app':
                cmd += self.filename
                if abbr != 'file':
                    delim = '.' if self.is_django else ':'
                    cmd += delim + self.cls
                    if abbr != 'class':
                        cmd += "." + self.method
        return cmd

    def show_coverage(self):
        """Show the coverage, if present"""
        self.vim.command("highlight TestMisses ctermbg=Yellow ctermfg=Black")
        self.vim.command("sign define test_misses text=NC texthl=TestMisses")
        # Read coverage data
        coverage_path = os.path.join(self.project_dir, '.coverage')
        print coverage_path
        c = coverage.coverage(coverage_path)
        c.data.read()
        for b in self.vim.buffers:
            tested_lines, _, missed_lines, missed_ranges = c.analysis(b.name)
            # If we have missed all files, this isn't worth to show
            if tested_lines != missed_lines:
                # We want to use missed_ranges to include nop-lines etc.
                missed = []
                for r in missed_ranges.split(', '):
                    start, end = [int(i) for i in r.split('-')]
                    missed += list(range(start, end+1))
                for line in missed:
                    self.vim.command(
                        "sign place {} line={} name=test_misses file={}"
                        .format(line, line, b.name))


def ShowTestResults(vim, file):
    # Define signs
    vim.command("sign define test_failed text=!! texthl=TestFailure")
    vim.command("sign define test_success text=() texthl=TestSuccess")
    vim.command("highlight link TestFailure error")
    vim.command("highlight TestSuccess ctermbg=Green")
    tree = ElementTree.parse(file)
    root = tree.getroot()
    tests = []
    for testcase in root.findall('testcase'):
        cls = testcase.get('classname').rsplit('.')[-1]
        status = 'success' if testcase.find('failure') is None else 'failed'
        tests.append({
            'class': cls,
            'name': testcase.get('name'),
            'time': testcase.get('time'),
            'status': status,
        })

    for b in vim.buffers:
        for num, line in enumerate(b[:100], start=1):
            for test in tests:
                test_str = "def {}(".format(test['name'])
                if test_str in line:
                    vim.command("sign place {} line={} name=test_{} file={}"
                                .format(num, num, test['status'], b.name))
