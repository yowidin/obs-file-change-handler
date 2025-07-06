from pydantic import ValidationError
from paramiko.ssh_exception import SSHException
import sys

from obs_file_change_handler.file_mover import FileMover
from obs_file_change_handler.single_instance import SingleInstance


def report_exception(e):
    print(e)
    sys.exit(-1)


def main():
    try:
        with SingleInstance():
            with FileMover.make() as mover:
                mover.run()
    except SSHException as e:
        report_exception(f'SSH Error: {e}')
    except ValidationError as e:
        report_exception(f'Validation Error: {e}')
    except KeyboardInterrupt:
        report_exception(f'Keyboard interrupt')
    except OSError as e:
        report_exception(f'OS Error: {e}')
    except RuntimeError as e:
        report_exception(f'Runtime Error: {e}')


if __name__ == "__main__":
    main()
