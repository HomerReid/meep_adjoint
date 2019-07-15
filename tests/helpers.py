"""Implementation of simple TestEnvironment helper class used in meep_adjoint tests.

   This file doesn't contribute any new test cases to the test suite, but just
   implements a helper class used by meep_adjoint test codes.
"""
import sys
import os
from os.path import expanduser, isfile
import shutil
from tempfile import TemporaryDirectory


class TestEnvironment(object):
    """ Context manager for setting up and tearing down an artificial
        environment for a test code, taking care to preserve any files
        that were present before we arrived but need to be temporarily
        removed and replaced by our mock versions for the duration of
        the test.

        More specifically, this class sets up
            (a) input files
            (b) environment variables
            (c) command-line options
        with the guarantee that any existing files that would be overwritten
        by step (a) are temporarily relocated on entry and restored on exit.

        Constructor inputs:
            test_files: list of (filename, filebody) tuples for input files that
                        should exist with the given content for the duration of the context.
            test_env:   dict of { var:value } records that should be present in
                        sys.environ for the duration of the context
            test_args:  dict of { arg:value } records that should be present in
                        sys.argv for the duration of the context

        Class data fields:
            self.files = list of (file_path,hideout) pairs.
                         file_path(str) is the full filesystem path of a
                         file created or overwritten for the test.
                         If that file existed within the filesystem
                         before we arrived, hideout(str) is the full
                         filesystem path of the safe location to which that file
                         has been temporarily relocated for safekeeping during
                         the test. In this case we restore the original file
                         on exit.
                         If the file did not exist in the filesystem before
                         we arrived, then on exit we simply delete the temporary
                         file at original_path.

            self.tmpdir = temporary directory in which pre-existing
                          files are stored, or None if there were no
                          pre-existing files
    """
    def __init__(self, test_files=[], test_env={}, test_args={}):

        # Step 1: Ensure that all required files exist with the
        # specified content, taking care to avoid rewriting existing files.
        self.files, self.tmpdir = [], None
        for nf, (name,body) in enumerate(test_files):
            file_path = expanduser(name)
            if isfile(file_path):
                self.tmpdir = self.tmpdir or TemporaryDirectory()
                hideout = '{}/f{}'.format(self.tmpdir.name,nf)
                shutil.move(file_path, hideout)
            else:
                hideout = None
            self.files += [(file_path,hideout)]
            with open(file_path,'w') as f:
                f.write(body)

        # Steps 2,3: Add environment variables and command-line arguments.
        os.environ.update( {k:str(v) for k,v in test_env.items() } )

        sys.argv=sys.argv[0:1]
        for (t,v) in test_args.items():
            sys.argv += ['--{}'.format(t)] + ( ['{}'.format(v)] if v else [] )


    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        """For all test files, restore the pre-existing
           version of the file, or simply delete it if the file
           did not previously exist. Then clean up the
           temporary directory, if we created one.
        """
        for (file_path,hideout) in self.files:
            if hideout is not None:
                shutil.move(hideout,file_path)
            else:
                os.remove(file_path)
        if self.tmpdir:
            self.tmpdir.cleanup()
