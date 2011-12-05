#!/usr/bin/python
#
# This is a poor-man's executable builder, for embedding dependencies into
# our pagekite.py file until we have proper packaging.
#
import base64, os, sys, zlib

BREEDER_PREAMBLE = """\
#!/usr/bin/python
#
# NOTE: This is a compilation of multiple Python files.
#       See below for details on individual segments.
#
import base64, imp, os, sys, StringIO, zlib

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
BREEDER_GTK_PREAMBLE = """\
try:
  import gobject, gtk
  def gtk_open_image(filename): return __FILES[filename]
except ImportError:
  pass

"""
BREEDER_POSTAMBLE = """\

#EOF#
"""

BREEDER_DIVIDER = '#' * 79


def br79(data):
  lines = []
  while len(data) > 0:
    lines.append(data[0:79])
    data = data[79:]
  return lines

def format_snake(fn, raw=False, compress=False, binary=False):
  fd = open(fn, 'rb')
  if raw:
    pre, post = '"""\\', '"""'
    lines = [l.replace('\n', '')
              .replace('\r', '')
             for l in fd.readlines()]
  elif compress:
    pre, post = 'zlib.decompress(base64.b64decode("""\\', '"""))'
    lines = br79(base64.b64encode(zlib.compress(''.join(fd.readlines()), 9)))
  elif binary:
    pre, post = 'base64.b64decode("""\\', '""")'
    lines = br79(base64.b64encode(''.join(fd.readlines())))
  else:
    pre, post = '"""\\', '"""'
    lines = [l.replace('\n', '')
              .replace('\r', '')
              .replace('\\', '\\\\')
              .replace('"', '\\"')
             for l in fd.readlines()]
  fd.close()
  return pre, lines, post

def breed_python(fn, main, compress=False):
  pre, lines, post = format_snake(fn, raw=main, compress=compress)
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

  text = ['__FILES[".SELF/%s"] = %s' % (fn, pre)]
  text.extend(lines)
  text.extend([
    post,
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

def breed_text(fn, compress=False):
  pre, lines, post = format_snake(fn, compress=compress)

  text = ['__FILES[".SELF/%s"] = %s' % (fn, pre)]
  text.extend(lines)
  text.append(post)

  return '\n'.join(text)

def breed_binary(fn, compress=False):
  pre, lines, post = format_snake(fn, compress=compress, binary=True)

  text = ['__FILES[".SELF/%s"] = %s' % (fn, pre)]
  text.extend(lines)
  text.append('%s\n' % post)

  return '\n'.join(text)

def breed_gtk_image(fn):
  img = gtk.Image()
  img.set_from_file(fn) 

  pb = img.get_pixbuf()
  lines = br79(base64.b64encode(zlib.compress(pb.get_pixels(), 9)))
  data = '\n'.join(lines)
  text = [('__FILES[".SELF/%s"] = \\\n  gtk.gdk.pixbuf_new_from_data(%s)'
           ) % (fn, ', '.join([str(p) for p in [
             'zlib.decompress(base64.b64decode("""\\\n%s"""\n  ))' % data,
             'gtk.gdk.COLORSPACE_RGB',
             pb.get_has_alpha(),
             pb.get_bits_per_sample(),
             pb.get_width(),
             pb.get_height(),
             pb.get_rowstride()
           ]])), '']

  return '\n'.join(text)


def breed_dir(dn, main, smart=True, gtk_images=False, compress=False):
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
    bred = breed(fn, ismain,
                 smart=True, gtk_images=gtk_images, compress=compress)
    if bred: text.append(bred)

  return ('\n%s\n' % BREEDER_DIVIDER).join(text)

EXCL = ('pyc', 'tmp', 'bak')
def breed(fn, main, smart=True, gtk_images=False, compress=False):
  if '"' in fn or '\\' in fn:
    raise ValueError('Cannot handle " or \\ in filenames')

  if os.path.isdir(fn):
    return breed_dir(fn, main,
                     smart=smart, gtk_images=gtk_images, compress=compress)

  extension = fn.split('.')[-1].lower()
  if smart and extension in EXCL: return ''

  if extension in ('py', 'pyw'):
    return breed_python(fn, main, compress=compress)

  if extension in ('txt', 'md', 'html', 'css', 'js', 'pk-shtml'):
    return breed_text(fn, compress=compress)

  if gtk_images and extension in ('gif', 'png', 'jpg', 'jpeg'):
    return breed_gtk_image(fn)

  return breed_binary(fn, compress=compress)


if __name__ == '__main__':
  gtk_images = compress = False

  args = sys.argv[1:]
  if '--gtk-images' in args:
    import gobject, gtk
    gtk_images = True
    args.remove('--gtk-images')
  if '--compress' in args:
    compress=True
    args.remove('--compress')

  print BREEDER_PREAMBLE
  if gtk_images:
    print BREEDER_GTK_PREAMBLE
  for fn in args:
    print BREEDER_DIVIDER
    print breed(fn, (fn == args[-1]), gtk_images=gtk_images, compress=compress)
    print
  print BREEDER_POSTAMBLE

