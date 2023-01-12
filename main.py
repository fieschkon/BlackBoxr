import sys

import BlackBoxr.BlackBoxr
from BlackBoxr import app
from BlackBoxr.modules.ExtensionLoader import ExtensionLoader

if __name__ == '__main__':
    
    ecode = BlackBoxr.BlackBoxr.main()
    app.shutdown(ecode)
    sys.exit(ecode)