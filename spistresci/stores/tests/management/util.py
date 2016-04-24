import sys
import contextlib

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from django.core.management import get_commands, load_command_class


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


def call_docopt_command(name, arg_string):
    arguments = ['manage.py', name] + arg_string.split(' ')

    command = get_command(name)

    with capture_standard_out() as out:
        command.run_from_argv(arguments)

    stdout, _ = out
    return stdout


def get_command(name):
    app_name = get_commands()[name]
    return load_command_class(app_name, name)
