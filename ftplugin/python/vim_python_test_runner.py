#!/bin/env python
import re
from os.path import splitext
from xml.etree import ElementTree


class TestCase(object):
    def __init__(self, vim):
        self.vim = vim
        self.buffer = vim.current.buffer
        self.current_line = vim.current.window.cursor[0]
        manage_py = "/opt/memoto/bump django"
        self.project_name = "memsite"
        self.basecommand = manage_py + ' test '

    @property
    def app(self):
        path = self.buffer.name
        components = path.split('/')
        app_index = components.index(self.project_name) + 1
        return components[app_index]

    @property
    def file(self):
        path = self.buffer.name
        app_file = path.split(self.app)[1].lstrip('/')
        basename = splitext(app_file)[0]
        return basename.replace('/', '.')

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
            components = [self.project_name]
            if abbr != 'project':
                components.append(self.app)
                if abbr != 'app':
                    components.append(self.file)
                    if abbr != 'file':
                        components.append(self.cls)
                        if abbr != 'class':
                            components.append(self.method)
            command = self.basecommand + '.'.join(components)
            self.vim.command("let g:last_test_command='{}'".format(command))
        return self.vim.eval('g:last_test_command')


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
