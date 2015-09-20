from testing.fun import *
from testing.work import *

try:
    print open('.SELF/README.md').read()
except (IOError, OSError):
    print "Rats, no README"

print Fun()
print Work()
