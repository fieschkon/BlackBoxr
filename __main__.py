import sys

import BlackBoxr.BlackBoxr
from BlackBoxr import app

if __name__ == '__main__':
    ecode = BlackBoxr.BlackBoxr.main()
    app.shutdown(ecode)
    sys.exit(ecode)