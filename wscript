#
# RTEMS Tools Project (http://www.rtems.org/)
# Copyright 2014-2015 Chris Johns (chrisj@rtems.org)
# All rights reserved.
#
# This file is part of the RTEMS Tools package in 'rtems-tools'.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import os.path

import wafwindows

subdirs = ['rtemstoolkit',
           'linkers',
           'tester',
           'tools/gdb/python']

def get_version(ctx):
    version = '4.12'
    revision = 'not_released'
    release = '%s.%s' % (version, revision)
    if os.path.exists('VERSION'):
        try:
            import configparser
        except ImportError:
            import ConfigParser as configparser
        v = configparser.SafeConfigParser()
        v.read('VERSION')
        release = v.get('version', 'release')
    else:
        from rtemstoolkit import git
        repo = git.repo('.')
        if repo.valid():
            head = repo.head()
            if repo.dirty():
                modified = '_modified'
            else:
                modified = ''
            release = '%s.%s%s' % (version, head[0:12], modified)
    last_dot = release.rfind('.')
    if last_dot == -1:
        ctx.fatal('invalid VERSION file')
    revision = release[0:last_dot]
    return revision, release

def recurse(ctx):
    for sd in subdirs:
        ctx.recurse(sd)

def options(ctx):
    ctx.add_option('--c-opts',
                   default = '-O2',
                   dest='c_opts',
                   help = 'Set build options, default: -O2.')
    ctx.add_option('--host',
                   default = 'native',
                   dest='host',
                   help = 'Set host to build for, default: none.')
    recurse(ctx)

def init(ctx):
    wafwindows.set_compilers()
    try:
        import waflib.Options
        import waflib.ConfigSet
        env = waflib.ConfigSet.ConfigSet()
        env.load(waflib.Options.lockfile)
        check_options(ctx, env.options['host'])
        recurse(ctx)
    except:
        pass

def shutdown(ctx):
    pass

def configure(ctx):
    try:
        ctx.load("doxygen", tooldir = 'waf-tools')
    except:
        pass
    ctx.env.RTEMS_VERSION, ctx.env.RTEMS_RELEASE = get_version(ctx)
    ctx.start_msg('Version')
    ctx.end_msg('%s (%s)' % (ctx.env.RTEMS_RELEASE, ctx.env.RTEMS_VERSION))
    ctx.env.C_OPTS = ctx.options.c_opts.split(',')
    check_options(ctx, ctx.options.host)
    #
    # Common Python check.
    #
    ctx.load('python')
    ctx.check_python_version((2,6,6))
    #
    # Installing the PYO,PYC seems broken on 1.8.19. The path is wrong.
    #
    ctx.env.PYO = 0
    ctx.env.PYC = 0
    recurse(ctx)

def build(ctx):
    if os.path.exists('VERSION'):
        ctx.install_files('${PREFIX}/share/rtems/rtemstoolkit', ['VERSION'])
    recurse(ctx)

def install(ctx):
    recurse(ctx)

def clean(ctx):
    recurse(ctx)

def rebuild(ctx):
    import waflib.Options
    waflib.Options.commands.extend(['clean', 'build'])

def check_options(ctx, host):
    if 'mingw32' in host:
        ctx.env.HOST = host
        ctx.env.CC = '%s-gcc' % (host)
        ctx.env.CXX = '%s-g++' % (host)
        ctx.env.AR = '%s-ar' % (host)
        ctx.env.PYTHON = 'python'
    elif host is not 'native':
        ctx.fatal('unknown host: %s' % (host));

#
# The doxy command.
#
from waflib import Build
class doxy(Build.BuildContext):
    fun = 'build'
    cmd = 'doxy'
