import argparse
import glob
import os
import os.path as op
from platform import system as sys_name
from stat import S_ISDIR
from setuptools_scm import get_version
import subprocess

from conda.cli.python_api import Commands, run_command
from paramiko import AutoAddPolicy, SSHClient

PLATFORMS = {
    "Windows": "win-64",
    "Darwin": "osx-64",
    "Linux": "linux-64"
}

PROXY_SERVER = "exflwgs06.desy.de:3128"
WHEEL_FILENAME = 'GUIExtensions-*.whl'
REMOTE_KARABO_DIR = "/var/www/html/karabo"

XDG_RUNTIME_DIR = "/tmp/runtime-root"
XVFB_ARGS = "-screen 0 1280x1024x24"
XVFB_DISPLAY = ":0"
XAUTHORITY_PATH = op.join(XDG_RUNTIME_DIR, ".Xauthority")

SSH_HOST = "exflserv05"
SSH_USER = "xkarabo"


class Builder:
    """Main Build Manager for the Karabo Control System
    Tailored for GUI Extensions

    Will take an argument module in input and will optionally clean, test, and
    upload the wheel to the desired destionation.
    """

    def __init__(self, args):
        # we get the root of the git repository here
        r = command_run(['git', 'rev-parse', '--show-toplevel'])
        self.root_path = op.normpath(r.decode().strip())
        self.args = args
        platform = PLATFORMS.get(sys_name())
        if platform is None:
            raise RuntimeError(f'Unsupported platform {sys_name()}')
        self.platform = platform
        self.version = get_version(self.root_path)

    def run(self):
        # Assume that there's only one recipe
        if not self.args.module:
            print("Nothing to do!")
            return

        # Check if nightly is enabled in the right mode
        if (self.args.nightly and
                os.environ.get("SCHEDULED_JOB", "") != "nightly-build"):
            print("Not a nightly-build scheduled job!")
            return

        # Check prebuild settings
        self.adapt_platform()
        if self.args.clean:
            self.clean()
        if self.args.test:
            self.run_tests()

        # Create and upload wheel
        if self.args.upload_wheel:
            filename = self.create_wheel()
            self.upload(filename)

    def adapt_platform(self):
        """Performs platform specific tasks per recipe"""
        if self.platform == 'osx-64':
            os.environ['LANG'] = 'en_US.UTF-8'
        elif self.platform == 'linux-64':
            # This is a CI specific setting
            proxy_server = os.environ.get('PROXY_SERVER') or PROXY_SERVER
            os.environ['http_proxy'] = f'http://{proxy_server}/'
            os.environ['https_proxy'] = f'https://{proxy_server}/'

            # Setup XVFB
            os.environ['DISPLAY'] = XVFB_DISPLAY
            os.environ['XDG_RUNTIME_DIR'] = XDG_RUNTIME_DIR
            os.environ['XAUTHORITY'] = XAUTHORITY_PATH
            command_run([
                'start-stop-daemon', '--start', '-b', '-x', '/usr/bin/Xvfb',
                '--', XVFB_DISPLAY, '-screen', '0', '1024x768x24'])

    def clean(self):
        """Cleans the environment of a package and purges old build dirs"""
        print("Cleaning", self.args.module)
        conda_run(
            Commands.RUN,
            '-n', 'base',
            'conda', 'build', 'purge-all')

        try:
            # Remove Karabo GUI environment
            conda_run(Commands.REMOVE, '-n', 'karabogui', '--all')
        except RuntimeError:
            # this might fail if the environment does not exist
            print("Tried removing `karabogui` environment, "
                  "but it does not exist")
            pass

        # Clean files that are not included in the branch
        # (potentially the Framework clone)
        command_run(['git', 'clean', '-fdx'])

    def run_tests(self):
        """We use the Framework master to test against with."""
        print(f"Running tests for {self.args.module}")
        token = os.environ.get('XFEL_TOKEN')
        git_path = f"https://{token}@git.xfel.eu/gitlab/Karabo/Framework.git"

        # Set git proxy
        http_proxy = os.environ.get('http_proxy') or f'http://{PROXY_SERVER}/'
        https_proxy = (os.environ.get('https_proxy')
                       or f'https://{PROXY_SERVER}/')
        command_run(['git', 'config', '--global', 'http.proxy', http_proxy])
        command_run(['git', 'config', '--global', 'https.proxy', https_proxy])
        # Clone Framework master
        framework_dir = op.join(self.root_path, 'Framework')
        command_run(['git', 'clone', git_path, framework_dir])

        # Create environment with Karabo GUI
        devenv_path = op.join('conda-recipes', 'karabogui',
                              'environment.devenv.yml')
        conda_run(Commands.RUN, '-n', 'base', 'conda', 'devenv',
                  '--file', op.join(framework_dir, devenv_path))

        # Install pythonGui in the environment to register the entrypoints
        gui_root = op.join(framework_dir, 'src', 'pythonGui')
        conda_run(Commands.RUN, '-n', 'karabogui', '--cwd', gui_root,
                  'python', 'setup.py', 'install')

        # Install pythonKarabo in the environment as well
        py_karabo_root = op.join(framework_dir, 'src', 'pythonKarabo')
        conda_run(Commands.RUN, '-n', 'karabogui', '--cwd', py_karabo_root,
                  'python', 'setup.py', 'install')

        # Then install the package
        conda_run(Commands.RUN, '-n', 'karabogui', '--cwd', self.root_path,
                  'python', 'setup.py', 'install')

        # Run tests
        cmd = [Commands.RUN, '-n', 'karabogui', 'pytest', '-v', '.']
        conda_run(*cmd)

        print('Tests successful')

    def create_wheel(self):
        print(f"Creating wheel at {os.environ.get('CI_PROJECT_DIR')}")
        command_run(['python', 'setup.py', 'bdist_wheel'])
        filename = op.join(self.root_path, '**', WHEEL_FILENAME)
        filenames = glob.glob(filename)
        # Verify if a wheel is created
        if not filenames:
            raise RuntimeError(f"GUIExtensions wheel is not found!")
        # Return filename of the created wheel, which usually is the
        # first (and only) hit
        return filenames[0]

    def upload(self, local_file_path):
        """Uploads the local file to in the in specified remote path"""
        remote_dir = '/'.join([self.args.remote_base_dir, str(self.version)])
        print("Creating remote directories:", remote_dir)

        with SSHClient() as ssh_client:
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            ssh_client.connect(hostname=SSH_HOST, username=SSH_USER,
                               password=os.environ.get("XKARABO_PWD"))
            with ssh_client.open_sftp() as sftp:
                # Create directory
                mkdir(remote_dir, basedir=REMOTE_KARABO_DIR, sftp=sftp)

                # Upload file
                filename = op.basename(local_file_path)
                remote_file_path = '/'.join(
                    [REMOTE_KARABO_DIR, remote_dir, filename])
                print(f'Uploading {local_file_path} to {remote_file_path}')
                sftp.put(local_file_path, remote_file_path)


def conda_run(command, *args, **kwargs):
    stdout, stderr, ret_code = run_command(command, *args, **kwargs)
    if ret_code != 0:
        msg = f'Command {command} [{args}] ' \
              f'{kwargs} returned {ret_code}\n{stderr}'
        raise RuntimeError(msg)
    return stdout


def command_run(cmd):
    try:
        return subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error in running command: {e.output}")
        raise e


def mkdir(remote_path, basedir='', sftp=None):
    rel_path = ''
    for path in remote_path.split('/'):
        rel_path = '/'.join([rel_path, path])
        abs_path = '/'.join([basedir, rel_path])
        try:
            stat_ = sftp.stat(abs_path)
            if not S_ISDIR(stat_.st_mode):
                raise RuntimeError(
                    f"{abs_path} exists and is not a directory.")
        except FileNotFoundError:
            print(f"Creating missing directory {abs_path}..")
            sftp.mkdir(abs_path)


def main(args):
    b = Builder(args)
    b.run()


DESCRIPTION = """
GUI Extensions Test and Build Manager

This script will manage the running of tests and uploading of the build wheel 
to the desired destination.
"""

if __name__ == '__main__':
    root_ap = argparse.ArgumentParser(
        description=DESCRIPTION)

    root_ap.add_argument('module', type=str)

    root_ap.add_argument(
        '-f', '--clean', action='store_true',
        help='clean development environment')

    root_ap.add_argument(
        '-T', '--test', action='store_true',
        help='run tests')

    root_ap.add_argument(
        '-N', '--nightly', action='store_true',
        help='check if this is a nightly build')

    root_ap.add_argument(
        '-U', '--upload-wheel', action='store_true',
        help='upload the wheel on remote host')

    root_ap.add_argument(
        '-P', '--remote-base-dir', type=str,
        default='karaboExtensions/tags',
        help='directory of the Extensions wheels on remote host.')

    args = root_ap.parse_args()
    main(args)
