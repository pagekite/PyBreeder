#!/usr/bin/python
#
# This is a poor-man's executable builder, for embedding dependencies into
# our pagekite.py file until we have proper packaging.
#
import os, sys

BREEDER_PREAMBLE = """\
#!/usr/bin/python
#
# NOTE: This is a compilation of multiple Python files.
#       See below for details on individual segments.
#
import imp, os, sys, StringIO

__FILES = {}
__os_path_exists = os.path.exists
__builtin_open = open

def __comb_open(filename, *args, **kwargs):
  if filename in __FILES:
    return StringIO.StringIO(__FILES[filename])
  else:
    return __builtin_open(filename, *args, **kwargs)

def __comb_exists(filename, *args, **kwargs):
  if filename in __FILES:
    return True
  else:
    return __os_path_exists(filename, *args, **kwargs)

open = __comb_open
os.path.exists = __comb_exists
sys.path[0:0] = ['.SELF/']

"""
BREEDER_POSTAMBLE = """\

#EOF#
"""

BREEDER_DIVIDER = '#' * 79


def breed_python(fn, main):
  fd = open(fn, 'rb')
  lines = [l.replace('\n', '').replace('\r', '') for l in fd.readlines()]
  fd.close()
  if main: return '\n'.join(lines)

  path = os.path.dirname(fn)
  if fn.endswith('/__init__.py'):
    bn = os.path.basename(path)
    path = path[:-len(bn)+1]
  else:
    bn = os.path.basename(fn).replace('.py', '')

  while path and os.path.exists(os.path.join(path, '__init__.py')):
    pbn = os.path.basename(path)
    bn = '%s.%s' % (pbn, bn)
    path = path[:-len(pbn)+1]

  text = ['__FILES[".SELF/%s"] = """\\' % fn]
  for line in lines:
    text.append('%s' % line.replace('\\', '\\\\').replace('"', '\\"'))
  text.extend([
    '"""',
    'sys.modules["%s"] = imp.new_module("%s")' % (bn, bn),
    'sys.modules["%s"].open = __comb_open' % (bn, ),
  ])
  if '.' in bn:
    parts = bn.split('.')
    text.append(('sys.modules["%s"].%s = sys.modules["%s"]'
                 ) % ('.'.join(parts[:-1]), parts[-1], bn))
  text.extend([
    'exec __FILES[".SELF/%s"] in sys.modules["%s"].__dict__' % (fn, bn),
    ''
  ])
  return '\n'.join(text)

def breed_text(fn):
  fd = open(fn, 'rb')
  lines = [l.replace('\n', '').replace('\r', '') for l in fd.readlines()]
  fd.close()

  text = ['__FILES[".SELF/%s"] = """\\' % fn]
  for line in lines:
    text.append('%s' % line.replace('\\', '\\\\').replace('"', '\\"'))

  return ''.join(text)

def breed_binary(fn):
  fd = open(fn, 'rb')
  lines = [l.replace('\n', '').replace('\r', '') for l in fd.readlines()]
  fd.close()

  text = ['__FILES[".SELF/%s"] = """\\' % fn]
  for line in lines:
    text.append('%s' % line.replace('\\', '\\\\').replace('"', '\\"'))

  return ''.join(text)

def breed_dir(dn, main):
  files = [f for f in os.listdir(dn) if not f.startswith('.')]
  text = []

  # Make sure __init__.py is FIRST.
  if '__init__.py' in files:
    files.remove('__init__.py')
    files[0:0] = ['__init__.py']

  # Make sure __main__.py is either excluded, or LAST
  if '__main__.py' in files:
    files.remove('__main__.py')
    if main: files.append('__main__.py')

  for fn in files:
    ismain = (main and fn == files[-1])
    fn = os.path.join(dn, fn)
    bred = breed(fn, ismain, smart=True)
    if bred: text.append(bred)

  return ('\n%s\n' % BREEDER_DIVIDER).join(text)

EXCL = ('pyc', 'tmp', 'bak')
def breed(fn, main, smart=False):
  if '"' in fn or '\\' in fn:
    raise ValueError('Cannot handle " or \\ in filenames')

  if os.path.isdir(fn):
    return breed_dir(fn, main)

  extension = fn.split('.')[-1].lower()
  if smart and extension in EXCL: return ''

  if extension in ('py', 'pyw'):
    return breed_python(fn, main)

  if extension in ('txt', 'md', 'html', 'css', 'js'):
    return breed_text(fn)

  return breed_binary(fn)


if __name__ == '__main__':
  print BREEDER_PREAMBLE
  for fn in sys.argv[1:]:
    print BREEDER_DIVIDER
    print breed(fn, main=(fn == sys.argv[-1]))
    print
  print BREEDER_POSTAMBLE

