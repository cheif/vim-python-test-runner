set makeprg=cat\ /tmp/test_results.txt
set efm+=%C\ %.%#,%A\ \ File\ \"%f\"\\,\ line\ %l%.%#,%Z%[%^\ ]%\\@=%m

if !has('python')
    finish
endif

" Show testresults after changing buffer
autocmd BufEnter * call ShowTestResultsAndCoverage()

" -----------------------------
" Add our directory to the path
" -----------------------------
python import sys
python import vim
python sys.path.append(vim.eval('expand("<sfile>:h")'))

function! RunDesiredTests(command_to_run)
python << endPython
import os
from sys import platform as _platform
from vim_python_test_runner import TestCase

def run_desired_command_for_os(command_to_run):
    if _platform == 'linux' or _platform == 'linux2':
        #vim.command(":Dispatch {0} 2>&1".format(command_to_run))
        vim.command(":call SendToTmux('{0}\n')".format(command_to_run))

def main():
    testcase = TestCase(vim)
    command_to_run = testcase.get_command(vim.eval("a:command_to_run"))
    run_desired_command_for_os(command_to_run)

vim.command('wall')
main()
endPython
endfunction

function! ShowTestResultsAndCoverage()
python << endPython
from vim_python_test_runner import TestCase
from vim_python_test_runner import ShowTestResults
case = TestCase(vim)
case.show_coverage()
ShowTestResults(vim, '/tmp/nosetests.xml')
endPython
endfunction

command! DjangoTestApp call RunDesiredTests("app")
command! DjangoTestClass call RunDesiredTests("class")
command! DjangoTestFile call RunDesiredTests("file")
command! DjangoTestMethod call RunDesiredTests("method")
command! DjangoTestProject call RunDesiredTests("project")
command! DjangoTestRerun call RunDesiredTests("rerun")

nnoremap <Leader>t :DjangoTestMethod<cr>
nnoremap <Leader>c :DjangoTestClass<cr>
nnoremap <Leader>f :DjangoTestFile<cr>
nnoremap <Leader>a :DjangoTestApp<cr>
nnoremap <Leader>* :DjangoTestProject<cr>
nnoremap <Leader>r :DjangoTestRerun<cr>
