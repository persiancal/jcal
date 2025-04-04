#!/usr/bin/python3
# Main VCSToChangeLog script.
# Copyright (C) 2019-2025 Free Software Foundation, Inc.
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# This modified version runs in a single file and is patched in a `PATCHED`
# section to prevent a NoneType.strip error.
#
# This was taken on April 4th 2025 from:
# https://git.savannah.gnu.org/cgit/gnulib.git/tree/build-aux/vcs-to-changelog.py
#
# See also:
# https://git.savannah.gnu.org/cgit/gnulib.git/tree/build-aux/gitlog-to-changelog

''' Generate a ChangeLog style output based on a VCS log.

This script takes two revisions as input and generates a ChangeLog style output
for all revisions between the two revisions.

This script is intended to be executed from the project parent directory.

The vcstocl directory has a file vcstocl_quirks.py that defines a
function called get_project_quirks that returns a object of class type
ProjectQuirks or a subclass of the same.  The definition of the ProjectQuirks
class is below and it specifies the properties that the project must set to
ensure correct parsing of its contents.

Among other things, ProjectQuirks specifies the VCS to read from; the default is
assumed to be git.  The script then studies the VCS log and for each change,
list out the nature of changes in the constituent files.

Each file type may have parser frontends that can read files and construct
objects that may be compared to determine the minimal changes that occurred in
each revision.  For files that do not have parsers, we may only know the nature
of changes at the top level depending on the information that the VCS stores.

The parser frontend must have a compare() method that takes the old and new
files as arrays of strings and prints the output in ChangeLog format.

Currently implemented VCS:

    git

Currently implemented frontends:

    C
'''

import sys
import os
import re
import argparse

class DebugUtil:
    debug = False
    def __init__(self, debug):
        self.debug = debug

    def eprint(self, *args, **kwargs):
        ''' Print to stderr.
        '''
        print(*args, file=sys.stderr, **kwargs)


    def print(self, *args, **kwargs):
        ''' Convenience function to print diagnostic information in the program.
        '''
        if self.debug:
            self.eprint(*args, **kwargs)


def decode(string):
    ''' Attempt to decode a string.

    Decode a string read from the source file.  The multiple attempts are needed
    due to the presence of the page break characters and some tests in locales.
    '''
    codecs = ['utf8', 'cp1252']

    for i in codecs:
        try:
            return string.decode(i)
        except UnicodeDecodeError:
            pass

    DebugUtil.eprint('Failed to decode: %s' % string)


def analyze_diff(filename, oldfile, newfile, frontends):
    ''' Parse the output of the old and new files and print the difference.

    For input files OLDFILE and NEWFILE with name FILENAME, generate reduced
    trees for them and compare them.  We limit our comparison to only C source
    files.
    '''
    name, ext = os.path.splitext(filename)

    if not ext in frontends.keys():
        return None
    else:
        frontend = frontends[ext]
        frontend.compare(oldfile, newfile)

from enum import Enum

class block_flags(Enum):
    ''' Flags for the code block.
    '''
    else_block = 1
    macro_defined = 2
    macro_redefined = 3


class block_type(Enum):
    ''' Type of code block.
    '''
    file = 1
    macro_cond = 2
    macro_def = 3
    macro_undef = 4
    macro_include = 5
    macro_info = 6
    decl = 7
    func = 8
    composite = 9
    macrocall = 10
    fndecl = 11
    assign = 12
    struct = 13
    union = 14
    enum = 15

# A dictionary describing what each action (add, modify, delete) show up as in
# the ChangeLog output.
actions = {0:{'new': 'New', 'mod': 'Modified', 'del': 'Remove'},
           block_type.file:{'new': 'New file', 'mod': 'Modified file',
                            'del': 'Remove file'},
           block_type.macro_cond:{'new': 'New', 'mod': 'Modified',
                                  'del': 'Remove'},
           block_type.macro_def:{'new': 'New', 'mod': 'Modified',
                                 'del': 'Remove'},
           block_type.macro_include:{'new': 'Include file', 'mod': 'Modified',
                                     'del': 'Remove include'},
           block_type.macro_info:{'new': 'New preprocessor message',
                                  'mod': 'Modified', 'del': 'Remove'},
           block_type.decl:{'new': 'New', 'mod': 'Modified', 'del': 'Remove'},
           block_type.func:{'new': 'New function', 'mod': 'Modified function',
                 'del': 'Remove function'},
           block_type.composite:{'new': 'New', 'mod': 'Modified',
                                 'del': 'Remove'},
           block_type.struct:{'new': 'New struct', 'mod': 'Modified struct',
                                 'del': 'Remove struct'},
           block_type.union:{'new': 'New union', 'mod': 'Modified union',
                                 'del': 'Remove union'},
           block_type.enum:{'new': 'New enum', 'mod': 'Modified enum',
                                 'del': 'Remove enum'},
           block_type.macrocall:{'new': 'New', 'mod': 'Modified',
                                 'del': 'Remove'},
           block_type.fndecl:{'new': 'New function', 'mod': 'Modified',
                              'del': 'Remove'},
           block_type.assign:{'new': 'New', 'mod': 'Modified', 'del': 'Remove'}}

def new_block(name, type, contents, parent, flags = 0):
    '''  Create a new code block with the parent as PARENT.

    The code block is a basic structure around which the tree representation of
    the source code is built.  It has the following attributes:

    - name: A name to refer it by in the ChangeLog
    - type: Any one of the following types in BLOCK_TYPE.
    - contents: The contents of the block.  For a block of types file or
      macro_cond, this would be a list of blocks that it nests.  For other types
      it is a list with a single string specifying its contents.
    - parent: This is the parent of the current block, useful in setting up
      #elif or #else blocks in the tree.
    - flags: A special field to indicate some properties of the block. See
      BLOCK_FLAGS for values.
    '''
    block = {}
    block['matched'] = False
    block['name'] = name
    block['type'] = type
    block['contents'] = contents
    block['parent'] = parent
    if parent:
        parent['contents'].append(block)

    block['flags'] = flags
    block['actions'] = actions[type]

    return block


class ExprParser:
    ''' Parent class of all of the C expression parsers.

    It is necessary that the children override the parse_line() method.
    '''
    ATTRIBUTE = r'(((__attribute__\s*\(\([^;]+\)\))|(asm\s*\([?)]+\)))\s*)*'

    def __init__(self, project_quirks, debug):
        self.project_quirks = project_quirks
        self.debug = debug

    def fast_forward_scope(self, cur, op, loc):
        ''' Consume lines in a code block.

        Consume all lines of a block of code such as a composite type declaration or
        a function declaration.

        - CUR is the string to consume this expression from
        - OP is the string array for the file
        - LOC is the first unread location in CUR

        - Returns: The next location to be read in the array as well as the updated
          value of CUR, which will now have the body of the function or composite
          type.
        '''
        nesting = cur.count('{') - cur.count('}')
        while nesting > 0 and loc < len(op):
            cur = cur + ' ' + op[loc]

            nesting = nesting + op[loc].count('{')
            nesting = nesting - op[loc].count('}')
            loc = loc + 1

        return (cur, loc)

    def parse_line(self, cur, op, loc, code, macros):
        ''' The parse method should always be overridden by the child.
        '''
        raise


class FuncParser(ExprParser):
    REGEX = re.compile(ExprParser.ATTRIBUTE + r'\s*(\w+)\s*\([^(][^{]+\)\s*{')

    def parse_line(self, cur, op, loc, code, macros):
        ''' Parse a function.

        Match a function definition.

        - CUR is the string to consume this expression from
        - OP is the string array for the file
        - LOC is the first unread location in CUR
        - CODE is the block to which we add this

        - Returns: The next location to be read in the array.
        '''
        found = re.search(self.REGEX, cur)
        if not found:
            return cur, loc

        name = found.group(5)
        self.debug.print('FOUND FUNC: %s' % name)

        # Consume everything up to the ending brace of the function.
        (cur, loc) = self.fast_forward_scope(cur, op, loc)

        new_block(name, block_type.func, [cur], code)

        return '', loc


class CompositeParser(ExprParser):
    # Composite types such as structs and unions.
    REGEX = re.compile(r'(struct|union|enum)\s*(\w*)\s*{')

    def parse_line(self, cur, op, loc, code, macros):
        ''' Parse a composite type.

        Match declaration of a composite type such as a sruct or a union..

        - CUR is the string to consume this expression from
        - OP is the string array for the file
        - LOC is the first unread location in CUR
        - CODE is the block to which we add this

        - Returns: The next location to be read in the array.
        '''
        found = re.search(self.REGEX, cur)
        if not found:
            return cur, loc

        # Lap up all of the struct definition.
        (cur, loc) = self.fast_forward_scope(cur, op, loc)

        name = found.group(2)

        if not name:
            if 'typedef' in cur:
                name = re.sub(r'.*}\s*(\w+);$', r'\1', cur)
            else:
                name= '<anonymous>'

        ctype = found.group(1)

        if ctype == 'struct':
            blocktype = block_type.struct
        if ctype == 'enum':
            blocktype = block_type.enum
        if ctype == 'union':
            blocktype = block_type.union

        new_block(name, block_type.composite, [cur], code)

        return '', loc


class AssignParser(ExprParser):
    # Static assignments.
    REGEX = re.compile(r'(\w+)\s*(\[[^\]]*\])*\s*([^\s]*attribute[\s\w()]+)?\s*=')

    def parse_line(self, cur, op, loc, code, macros):
        ''' Parse an assignment statement.

        This includes array assignments.

        - CUR is the string to consume this expression from
        - OP is the string array for the file
        - LOC is the first unread location in CUR
        - CODE is the block to which we add this

        - Returns: The next location to be read in the array.
        '''
        found = re.search(self.REGEX, cur)
        if not found:
            return cur, loc

        name = found.group(1)
        self.debug.print('FOUND ASSIGN: %s' % name)
        # Lap up everything up to semicolon.
        while ';' not in cur and loc < len(op):
            cur = op[loc]
            loc = loc + 1

        new_block(name, block_type.assign, [cur], code)

        return '', loc


class DeclParser(ExprParser):
    # Function pointer typedefs.
    TYPEDEF_FN_RE = re.compile(r'\(\*(\w+)\)\s*\([^)]+\);')

    # Simple decls.
    DECL_RE = re.compile(r'(\w+)(\[\w*\])*\s*' + ExprParser.ATTRIBUTE + ';')

    # __typeof decls.
    TYPEOF_RE = re.compile(r'__typeof\s*\([\w\s]+\)\s*(\w+)\s*' + \
                           ExprParser.ATTRIBUTE + ';')

    # Function Declarations.
    FNDECL_RE = re.compile(r'\s*(\w+)\s*\(([^\(][^;]*)?\)\s*' +
                           ExprParser.ATTRIBUTE + ';')

    def __init__(self, regex, blocktype, project_quirks, debug):
        # The regex for the current instance.
        self.REGEX = regex
        self.blocktype = blocktype
        super().__init__(project_quirks, debug)

    def parse_line(self, cur, op, loc, code, macros):
        ''' Parse a top level declaration.

        All types of declarations except function declarations.

        - CUR is the string to consume this expression from
        - OP is the string array for the file
        - LOC is the first unread location in CUR
        - CODE is the block to which we add this function

        - Returns: The next location to be read in the array.
        '''
        found = re.search(self.REGEX, cur)
        if not found:
            return cur, loc

        # The name is the first group for all of the above regexes.  This is a
        # coincidence, so care must be taken if regexes are added or changed to
        # ensure that this is true.
        name = found.group(1)

        self.debug.print('FOUND DECL: %s' % name)
        new_block(name, self.blocktype, [cur], code)

        return '', loc


class MacroParser(ExprParser):
    # The macrocall_re peeks into the next line to ensure that it doesn't
    # eat up a FUNC by accident.  The func_re regex is also quite crude and
    # only intends to ensure that the function name gets picked up
    # correctly.
    MACROCALL_RE = re.compile(r'(\w+)\s*(\(.*\))*$')

    def parse_line(self, cur, op, loc, code, macros):
        ''' Parse a macro call.

        Match a symbol hack macro calls that get added without semicolons.

        - CUR is the string to consume this expression from
        - OP is the string array for the file
        - LOC is the first unread location in CUR
        - CODE is the block to which we add this
        - MACROS is the regex match object.

        - Returns: The next location to be read in the array.
        '''

        # First we have the macros for symbol hacks and all macros we identified so
        # far.
        if cur.count('(') != cur.count(')'):
            return cur, loc
        if loc < len(op) and '{' in op[loc]:
            return cur, loc

        found = re.search(self.MACROCALL_RE, cur)
        if found:
            sym = found.group(1)
            name = found.group(2)
            if sym in macros or self.project_quirks and \
                    sym in self.project_quirks.C_MACROS:
                self.debug.print('FOUND MACROCALL: %s (%s)' % (sym, name))
                new_block(sym, block_type.macrocall, [cur], code)
                return '', loc

        # Next, there could be macros that get called right inside their #ifdef, but
        # without the semi-colon.
        if cur.strip() == code['name'].strip():
            self.debug.print('FOUND MACROCALL (without brackets): %s' % (cur))
            new_block(cur, block_type.macrocall, [cur], code)
            return '',loc

        return cur, loc


class Frontend:
    ''' The C Frontend implementation.
    '''
    KNOWN_MACROS = []

    def __init__(self, project_quirks, debug):
        self.op = []
        self.debug = debug
        self.project_quirks = project_quirks

        self.c_expr_parsers = [
                CompositeParser(project_quirks, debug),
                AssignParser(project_quirks, debug),
                DeclParser(DeclParser.TYPEOF_RE, block_type.decl,
                           project_quirks, debug),
                DeclParser(DeclParser.TYPEDEF_FN_RE, block_type.decl,
                           project_quirks, debug),
                DeclParser(DeclParser.FNDECL_RE, block_type.fndecl,
                           project_quirks, debug),
                FuncParser(project_quirks, debug),
                DeclParser(DeclParser.DECL_RE, block_type.decl, project_quirks,
                           debug),
                MacroParser(project_quirks, debug)]


    def remove_extern_c(self):
        ''' Process extern "C"/"C++" block nesting.

        The extern "C" nesting does not add much value so it's safe to almost always
        drop it.  Also drop extern "C++"
        '''
        new_op = []
        nesting = 0
        extern_nesting = 0
        for l in self.op:
            if '{' in l:
                nesting = nesting + 1
            if re.match(r'extern\s*"C"\s*{', l):
                extern_nesting = nesting
                continue
            if '}' in l:
                nesting = nesting - 1
                if nesting < extern_nesting:
                    extern_nesting = 0
                    continue
            new_op.append(l)

        # Now drop all extern C++ blocks.
        self.op = new_op
        new_op = []
        nesting = 0
        extern_nesting = 0
        in_cpp = False
        for l in self.op:
            if re.match(r'extern\s*"C\+\+"\s*{', l):
                nesting = nesting + 1
                in_cpp = True

            if in_cpp:
                if '{' in l:
                    nesting = nesting + 1
                if '}' in l:
                    nesting = nesting - 1
            if nesting == 0:
                new_op.append(l)

        self.op = new_op


    def remove_comments(self, op):
        ''' Remove comments.

        Return OP by removing all comments from it.
        '''
        self.debug.print('REMOVE COMMENTS')

        sep='\n'
        opstr = sep.join(op)
        opstr = re.sub(r'/\*.*?\*/', r'', opstr, flags=re.MULTILINE | re.DOTALL)
        opstr = re.sub(r'\\\n', r' ', opstr, flags=re.MULTILINE | re.DOTALL)
        new_op = list(filter(None, opstr.split(sep)))

        return new_op


    def normalize_condition(self, name):
        ''' Make some minor transformations on macro conditions to make them more
        readable.
        '''
        # Negation with a redundant bracket.
        name = re.sub(r'!\s*\(\s*(\w+)\s*\)', r'! \1', name)
        # Pull in negation of equality.
        name = re.sub(r'!\s*\(\s*(\w+)\s*==\s*(\w+)\)', r'\1 != \2', name)
        # Pull in negation of inequality.
        name = re.sub(r'!\s*\(\s*(\w+)\s*!=\s*(\w+)\)', r'\1 == \2', name)
        # Fix simple double negation.
        name = re.sub(r'!\s*\(\s*!\s*(\w+)\s*\)', r'\1', name)
        # Similar, but nesting a complex expression.  Because of the greedy match,
        # this matches only the outermost brackets.
        name = re.sub(r'!\s*\(\s*!\s*\((.*)\)\s*\)$', r'\1', name)
        return name


    def parse_preprocessor(self, loc, code, start = ''):
        ''' Parse a preprocessor directive.

        In case a preprocessor condition (i.e. if/elif/else), create a new code
        block to nest code into and in other cases, identify and add entities such as
        include files, defines, etc.

        - OP is the string array for the file
        - LOC is the first unread location in CUR
        - CODE is the block to which we add this function
        - START is the string that should continue to be expanded in case we step
          into a new macro scope.

        - Returns: The next location to be read in the array.
        '''
        cur = self.op[loc]
        loc = loc + 1
        endblock = False

        self.debug.print('PARSE_MACRO: %s' % cur)

        # Remove the # and strip spaces again.
        cur = cur[1:].strip()

        # Include file.
        if cur.find('include') == 0:
            m = re.search(r'include\s*["<]?([^">]+)[">]?', cur)
            new_block(m.group(1), block_type.macro_include, [cur], code)

        # Macro definition.
        if cur.find('define') == 0:
            m = re.search(r'define\s+([a-zA-Z0-9_]+)', cur)
            name = m.group(1)
            exists = False
            # Find out if this is a redefinition.
            for c in code['contents']:
                if c['name'] == name and c['type'] == block_type.macro_def:
                    c['flags'] = block_flags.macro_redefined
                    exists = True
                    break
            if not exists:
                new_block(m.group(1), block_type.macro_def, [cur], code,
                          block_flags.macro_defined)
                # Add macros as we encounter them.
                self.KNOWN_MACROS.append(m.group(1))

        # Macro undef.
        if cur.find('undef') == 0:
            m = re.search(r'undef\s+([a-zA-Z0-9_]+)', cur)
            new_block(m.group(1), block_type.macro_def, [cur], code)

        # #error and #warning macros.
        if cur.find('error') == 0 or cur.find('warning') == 0:
            m = re.search(r'(error|warning)\s+"?(.*)"?', cur)
            if m:
                name = m.group(2)
            else:
                name = '<blank>'
            new_block(name, block_type.macro_info, [cur], code)

        # Start of an #if or #ifdef block.
        elif cur.find('if') == 0:
            rem = re.sub(r'ifndef', r'!', cur).strip()
            rem = re.sub(r'(ifdef|defined|if)', r'', rem).strip()
            rem = self.normalize_condition(rem)
            ifdef = new_block(rem, block_type.macro_cond, [], code)
            ifdef['headcond'] = ifdef
            ifdef['start'] = start
            loc = self.parse_line(loc, ifdef, start)

        # End the previous #if/#elif and begin a new block.
        elif cur.find('elif') == 0 and code['parent']:
            rem = self.normalize_condition(re.sub(r'(elif|defined)', r'', cur).strip())
            # The #else and #elif blocks should go into the current block's parent.
            ifdef = new_block(rem, block_type.macro_cond, [], code['parent'])
            ifdef['headcond'] = code['headcond']
            loc = self.parse_line(loc, ifdef, code['headcond']['start'])
            endblock = True

        # End the previous #if/#elif and begin a new block.
        elif cur.find('else') == 0 and code['parent']:
            name = self.normalize_condition('!(' + code['name'] + ')')
            ifdef = new_block(name, block_type.macro_cond, [], code['parent'],
                              block_flags.else_block)
            ifdef['headcond'] = code['headcond']
            loc = self.parse_line(loc, ifdef, code['headcond']['start'])
            endblock = True

        elif cur.find('endif') == 0 and code['parent']:
            # Insert an empty else block if there isn't one.
            if code['flags'] != block_flags.else_block:
                name = self.normalize_condition('!(' + code['name'] + ')')
                ifdef = new_block(name, block_type.macro_cond, [], code['parent'],
                                  block_flags.else_block)
                ifdef['headcond'] = code['headcond']
                loc = self.parse_line(loc - 1, ifdef, code['headcond']['start'])
            endblock = True

        return (loc, endblock)


    def parse_c_expr(self, cur, loc, code):
        ''' Parse a C expression.

        CUR is the string to be parsed, which continues to grow until a match is
        found.  OP is the string array and LOC is the first unread location in the
        string array.  CODE is the block in which any identified expressions should
        be added.
        '''
        self.debug.print('PARSING: %s' % cur)

        for p in self.c_expr_parsers:
            cur, loc = p.parse_line(cur, self.op, loc, code, self.KNOWN_MACROS)
            if not cur:
                break

        return cur, loc


    def expand_problematic_macros(self, cur):
        ''' Replace problem macros with their substitutes in CUR.
        '''
        for p in self.project_quirks.MACRO_QUIRKS:
            cur = re.sub(p['orig'], p['sub'], cur)

        return cur


    def parse_line(self, loc, code, start = ''):
        '''
        Parse the file line by line.  The function assumes a mostly GNU coding
        standard compliant input so it might barf with anything that is eligible for
        the Obfuscated C code contest.

        The basic idea of the parser is to identify macro conditional scopes and
        definitions, includes, etc. and then parse the remaining C code in the
        context of those macro scopes.  The parser does not try to understand the
        semantics of the code or even validate its syntax.  It only records high
        level symbols in the source and makes a tree structure to indicate the
        declaration/definition of those symbols and their scope in the macro
        definitions.

        OP is the string array.
        LOC is the first unparsed line.
        CODE is the block scope within which the parsing is currently going on.
        START is the string with which this parsing should start.
        '''
        cur = start
        endblock = False
        saved_cur = ''
        saved_loc = 0
        endblock_loc = loc

        while loc < len(self.op):
            nextline = self.op[loc]

            # Macros.
            if nextline[0] == '#':
                (loc, endblock) = self.parse_preprocessor(loc, code, cur)
                if endblock:
                    endblock_loc = loc
            # Rest of C Code.
            else:
                cur = cur + ' ' + nextline
                cur = self.expand_problematic_macros(cur).strip()
                cur, loc = self.parse_c_expr(cur, loc + 1, code)

            if endblock and not cur:
                # If we are returning from the first #if block, we want to proceed
                # beyond the current block, not repeat it for any preceding blocks.
                if code['headcond'] == code:
                    return loc
                else:
                    return endblock_loc

        return loc

    def drop_empty_blocks(self, tree):
        ''' Drop empty macro conditional blocks.
        '''
        newcontents = []

        for x in tree['contents']:
            if x['type'] != block_type.macro_cond or len(x['contents']) > 0:
                newcontents.append(x)

        for t in newcontents:
            if t['type'] == block_type.macro_cond:
                self.drop_empty_blocks(t)

        tree['contents'] = newcontents


    def consolidate_tree_blocks(self, tree):
        ''' Consolidate common macro conditional blocks.

        Get macro conditional blocks at the same level but scattered across the
        file together into a single common block to allow for better comparison.
        '''
        # Nothing to do for non-nesting blocks.
        if tree['type'] != block_type.macro_cond \
                and tree['type'] != block_type.file:
            return

        # Now for nesting blocks, get the list of unique condition names and
        # consolidate code under them.  The result also bunches up all the
        # conditions at the top.
        newcontents = []

        macros = [x for x in tree['contents'] \
                  if x['type'] == block_type.macro_cond]
        macro_names = sorted(set([x['name'] for x in macros]))
        for m in macro_names:
            nc = [x['contents'] for x in tree['contents'] if x['name'] == m \
                    and x['type'] == block_type.macro_cond]
            b = new_block(m, block_type.macro_cond, sum(nc, []), tree)
            self.consolidate_tree_blocks(b)
            newcontents.append(b)

        newcontents.extend([x for x in tree['contents'] \
                            if x['type'] != block_type.macro_cond])

        tree['contents'] = newcontents


    def compact_tree(self, tree):
        ''' Try to reduce the tree to its minimal form.

        A source code tree in its simplest form may have a lot of duplicated
        information that may be difficult to compare and come up with a minimal
        difference.
        '''

        # First, drop all empty blocks.
        self.drop_empty_blocks(tree)

        # Macro conditions that nest the entire file aren't very interesting.  This
        # should take care of the header guards.
        if tree['type'] == block_type.file \
                and len(tree['contents']) == 1 \
                and tree['contents'][0]['type'] == block_type.macro_cond:
            tree['contents'] = tree['contents'][0]['contents']

        # Finally consolidate all macro conditional blocks.
        self.consolidate_tree_blocks(tree)


    def parse(self, op):
        ''' File parser.

        Parse the input array of lines OP and generate a tree structure to
        represent the file.  This tree structure is then used for comparison between
        the old and new file.
        '''
        self.KNOWN_MACROS = []
        tree = new_block('', block_type.file, [], None)
        self.op = self.remove_comments(op)
        self.remove_extern_c()
        self.op = [re.sub(r'#\s+', '#', x) for x in self.op]
        self.parse_line(0, tree)
        self.compact_tree(tree)
        self.dump_tree(tree, 0)

        return tree


    def print_change(self, tree, action, prologue = ''):
        ''' Print the nature of the differences found in the tree compared to the
        other tree.  TREE is the tree that changed, action is what the change was
        (Added, Removed, Modified) and prologue specifies the macro scope the change
        is in.  The function calls itself recursively for all macro condition tree
        nodes.
        '''

        if tree['type'] != block_type.macro_cond:
            print('\t%s(%s): %s.' % (prologue, tree['name'], action))
            return

        prologue = '%s[%s]' % (prologue, tree['name'])
        for t in tree['contents']:
            if t['type'] == block_type.macro_cond:
                self.print_change(t, action, prologue)
            else:
                print('\t%s(%s): %s.' % (prologue, t['name'], action))


    def compare_trees(self, left, right, prologue = ''):
        ''' Compare two trees and print the difference.

        This routine is the entry point to compare two trees and print out their
        differences.  LEFT and RIGHT will always have the same name and type,
        starting with block_type.file and '' at the top level.
        '''

        if left['type'] == block_type.macro_cond or left['type'] == block_type.file:

            if left['type'] == block_type.macro_cond:
                prologue = '%s[%s]' % (prologue, left['name'])

            # Make sure that everything in the left tree exists in the right tree.
            for cl in left['contents']:
                found = False
                for cr in right['contents']:
                    if not cl['matched'] and not cr['matched'] and \
                            cl['name'] == cr['name'] and cl['type'] == cr['type']:
                        cl['matched'] = cr['matched'] = True
                        self.compare_trees(cl, cr, prologue)
                        found = True
                        break
                if not found:
                    self.print_change(cl, cl['actions']['del'], prologue)

            # ... and vice versa.  This time we only need to look at unmatched
            # contents.
            for cr in right['contents']:
                if not cr['matched']:
                    self.print_change(cr, cr['actions']['new'], prologue)
        else:
            if left['contents'] != right['contents']:
                self.print_change(left, left['actions']['mod'], prologue)


    def dump_tree(self, tree, indent):
        ''' Print the entire tree.
        '''
        if not self.debug.debug:
            return

        if tree['type'] == block_type.macro_cond or tree['type'] == block_type.file:
            print('%sScope: %s' % (' ' * indent, tree['name']))
            for c in tree['contents']:
                self.dump_tree(c, indent + 4)
            print('%sEndScope: %s' % (' ' * indent, tree['name']))
        else:
            if tree['type'] == block_type.func:
                print('%sFUNC: %s' % (' ' * indent, tree['name']))
            elif tree['type'] == block_type.composite:
                print('%sCOMPOSITE: %s' % (' ' * indent, tree['name']))
            elif tree['type'] == block_type.assign:
                print('%sASSIGN: %s' % (' ' * indent, tree['name']))
            elif tree['type'] == block_type.fndecl:
                print('%sFNDECL: %s' % (' ' * indent, tree['name']))
            elif tree['type'] == block_type.decl:
                print('%sDECL: %s' % (' ' * indent, tree['name']))
            elif tree['type'] == block_type.macrocall:
                print('%sMACROCALL: %s' % (' ' * indent, tree['name']))
            elif tree['type'] == block_type.macro_def:
                print('%sDEFINE: %s' % (' ' * indent, tree['name']))
            elif tree['type'] == block_type.macro_include:
                print('%sINCLUDE: %s' % (' ' * indent, tree['name']))
            elif tree['type'] == block_type.macro_undef:
                print('%sUNDEF: %s' % (' ' * indent, tree['name']))
            else:
                print('%sMACRO LEAF: %s' % (' ' * indent, tree['name']))


    def compare(self, oldfile, newfile):
        ''' Entry point for the C backend.

        Parse the two files into trees and compare them.  Print the result of the
        comparison in the ChangeLog-like format.
        '''
        self.debug.print('LEFT TREE')
        self.debug.print('-' * 80)
        left = self.parse(oldfile)

        self.debug.print('RIGHT TREE')
        self.debug.print('-' * 80)
        right = self.parse(newfile)

        self.compare_trees(left, right)


import subprocess
class GitRepo:
    def __init__(self, ignore_list, debug):
        self.ignore_list = ignore_list
        self.debug = debug


    def exec_git_cmd(self, args):
        ''' Execute a git command and return its result as a list of strings.
        '''
        args.insert(0, 'git')
        self.debug.print(args)
        proc = subprocess.Popen(args, stdout=subprocess.PIPE)

        # Clean up the output by removing trailing spaces, newlines and dropping
        # blank lines.
        # PATCHED (will not throw None does not have strip)
        op = []
        for i in proc.stdout:
            i = decode(i[:-1])
            if i is None:
                continue
            i = re.sub(r'[ \f]+', ' ', i.strip())
            if i:
                op.append(i)
        return op


    def list_changes(self, commit, frontends):
        ''' List changes in a single commit.

        For the input commit id COMMIT, identify the files that have changed and the
        nature of their changes.  Print commit information in the ChangeLog format,
        calling into helper functions as necessary.
        '''

        op = self.exec_git_cmd(['show', '--pretty=fuller', '--date=short',
                                '--raw', commit])
        authors = []
        date = ''
        merge = False
        copyright_exempt=''
        subject= ''

        for l in op:
            if l.lower().find('copyright-paperwork-exempt:') == 0 \
                    and 'yes' in l.lower():
                copyright_exempt=' (tiny change)'
            elif l.lower().find('co-authored-by:') == 0 or \
                    l.find('Author:') == 0:
                author = l.split(':')[1]
                author = re.sub(r'([^ ]*)\s*(<.*)', r'\1  \2', author.strip())
                authors.append(author)
            elif l.find('CommitDate:') == 0:
                date = l[11:].strip()
            elif l.find('Merge:') == 0:
                merge = True
            elif not subject and date:
                subject = l.strip()

        # Find raw commit information for all non-ChangeLog files.
        op = [x[1:] for x in op if len(x) > 0 and re.match(r'^:[0-9]+', x)]

        # Skip all ignored files.
        for ign in self.ignore_list:
            op = [x for x in op if ign not in x]

        # It was only the ChangeLog, ignore.
        if len(op) == 0:
            return

        print('%s  %s' % (date, authors[0]))

        if (len(authors) > 1):
            authors = authors[1:]
            for author in authors:
                print('            %s' % author)

        print()

        if merge:
           print('\t MERGE COMMIT: %s\n' % commit)
           return

        print('\tCOMMIT%s: %s\n\t%s\n' % (copyright_exempt, commit, subject))

        # Changes across a large number of files are typically mechanical (URL
        # updates, copyright notice changes, etc.) and likely not interesting
        # enough to produce a detailed ChangeLog entry.
        if len(op) > 100:
            print('\t* Suppressing diff as too many files differ.\n')
            return

        # Each of these lines has a space separated format like so:
        # :<OLD MODE> <NEW MODE> <OLD REF> <NEW REF> <OPERATION> <FILE1> <FILE2>
        #
        # where OPERATION can be one of the following:
        # A: File added
        # D: File removed
        # M[0-9]{3}: File modified
        # R[0-9]{3}: File renamed, with the 3 digit number following it indicating
        # what percentage of the file is intact.
        # C[0-9]{3}: File copied.  Same semantics as R.
        # T: The permission bits of the file changed
        # U: Unmerged.  We should not encounter this, so we ignore it/
        # X, or anything else: Most likely a bug.  Report it.
        #
        # FILE2 is set only when OPERATION is R or C, to indicate the new file name.
        #
        # Also note that merge commits have a different format here, with three
        # entries each for the modes and refs, but we don't bother with it for now.
        #
        # For more details: https://git-scm.com/docs/diff-format
        for f in op:
            data = f.split('\t')
            file1 = data[1]
            if len(data) > 2:
                file2 = data[2]

            data = data[0].split()

            if data[4] == 'A':
                print('\t* %s: New file.' % file1)
            elif data[4] == 'D':
                print('\t* %s: Delete file.' % file1)
            elif data[4] == 'T':
                print('\t* %s: Changed file permission bits from %s to %s' % \
                        (file1, data[0], data[1]))
            elif data[4][0] == 'M':
                print('\t* %s: Modified.' % file1)
                analyze_diff(file1,
                             self.exec_git_cmd(['show', data[2]]),
                             self.exec_git_cmd(['show', data[3]]), frontends)
            elif data[4][0] == 'R' or data[4][0] == 'C':
                change = int(data[4][1:])
                print('\t* %s: Move to...' % file1)
                print('\t* %s: ... here.' % file2)
                if change < 100:
                    analyze_diff(file2,
                                 self.exec_git_cmd(['show', data[2]]),
                                 self.exec_git_cmd(['show', data[3]]), frontends)
            # We should never encounter this, so ignore for now.
            elif data[4] == 'U':
                pass
            else:
                eprint('%s: Unknown line format %s' % (commit, data[4]))
                sys.exit(42)

        print('')


    def list_commits(self, revs):
        ''' List commit IDs between the two revs in the REVS list.
        '''
        ref = revs[0] + '..' + revs[1]
        return self.exec_git_cmd(['log', '--pretty=%H', ref])

class ProjectQuirks:
    ''' Base class for project quirks

    The following members can be overridden in the subclass:

    - MACRO_QUIRKS
      A list of dictionary entries with indexes as `orig` and `sub` where `orig`
      is a Python regular expression pattern to match and `sub` is the
      substitution.  These substitutions are used to work around C/C++ macros
      that are known to break parsing of C programs.

    - C_MACROS
      This is a list of macro definitions that are extensively used and are
      known to break parsing due to some characteristic, mainly the lack of a
      semicolon at the end.

    - IGNORE_LIST
      A list of files to ignore in the changesets, either because they are not
      needed (such as the ChangeLog) or because they are not parseable.  For
      example, glibc has a header file that is only assembly code, which breaks
      the C parser.

    - repo
      Specify the project repo source control.  The default value is `git`.

    '''
    MACRO_QUIRKS = []
    C_MACROS = []
    repo = 'git'
    IGNORE_LIST = ['ChangeLog']

debug = DebugUtil(False)

sys.path.append('/'.join([os.path.dirname(os.path.realpath(__file__)),
                'vcstocl']))

def main(repo, frontends, refs):
    ''' ChangeLog Generator Entry Point.
    '''
    commits = repo.list_commits(args.refs)
    for commit in commits:
        repo.list_changes(commit, frontends)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('refs', metavar='ref', type=str, nargs=2,
                     help='Refs to print ChangeLog entries between')

    parser.add_argument('-d', '--debug', required=False, action='store_true',
                     help='Run the file parser debugger.')

    parser.add_argument('-q', '--quirks', required=False, type=str,
                     help='Load a quirks file.')

    args = parser.parse_args()

    debug.debug = args.debug

    if len(args.refs) < 2:
        debug.eprint('Two refs needed to get a ChangeLog.')
        sys.exit(os.EX_USAGE)

    # Load quirks file.  We assume that the script is run from the top level source
    # directory.
    if args.quirks:
        import importlib.util
        spec = importlib.util.spec_from_file_location("vcstocl_quirks", args.quirks)
        vcstocl_quirks = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vcstocl_quirks)
        project_quirks = vcstocl_quirks.get_project_quirks(debug)
    else:
        try:
            from vcstocl_quirks import *
            project_quirks = get_project_quirks(debug)
        except:
            project_quirks = ProjectQuirks()

    REPO = {'git': GitRepo(project_quirks.IGNORE_LIST, debug)}

    fe_c = Frontend(project_quirks, debug)
    FRONTENDS = {'.c': fe_c,
                 '.h': fe_c}

    main(REPO[project_quirks.repo], FRONTENDS, args.refs)
