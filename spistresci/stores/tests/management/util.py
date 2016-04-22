import sys
import contextlib

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


@contextlib.contextmanager
def capture_standard_out():
    """
    Capture stdout and stderr. Returns list with [stdout, stderr]
    with capture_standard_out() as out:
        # do stuff
        pass
    stdout, stderr = out
    """
    previous_stdout = sys.stdout
    previous_stderr = sys.stderr

    out_stdout = StringIO()
    out_stderr = StringIO()
    out = [out_stdout, out_stderr]

    try:
        sys.stdout = out[0]
        sys.stderr = out[1]

        yield out
    finally:
        out[0] = out[0].getvalue()
        out[1] = out[1].getvalue()

        sys.stdout.close()
        sys.stdout = previous_stdout

        sys.stderr.close()
        sys.stderr = previous_stderr
