import os
import sys
import paramiko

from argparse import ArgumentParser
from pathlib import Path

from dateutil.parser import parse
from tqdm import tqdm

from obs_file_change_handler.config import Config


class FileMover:
    def __init__(self, config: Config, new_file: Path, verbose: bool, dry_run: bool):
        self.config = config
        self.new_file = Path(new_file)
        self.verbose = verbose
        self.dry_run = dry_run

        self.ssh_client = None  # type: paramiko.SSHClient | None
        self.sftp_client = None  # type: paramiko.SFTPClient | None

    def log(self, text: str):
        if self.verbose:
            print(text)

    def __enter__(self):
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.ssh_client.connect(
            hostname=self.config.ssh.host,
            port=self.config.ssh.port,
            username=self.config.ssh.username,
            password=self.config.ssh.password,
            key_filename=str(self.config.ssh.private_key),
        )

        self.sftp_client = self.ssh_client.open_sftp()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sftp_client is not None:
            self.sftp_client.close()
            self.sftp_client = None

        if self.ssh_client is not None:
            self.ssh_client.close()
            self.sftp_client = None

    @staticmethod
    def make() -> 'FileMover':
        config_file = Path('obs-file-change-config.toml').absolute()

        parser = ArgumentParser('OBS File Change Handler')
        parser.add_argument('--verbose', '-v', action='store_true', required=False, help='Verbose output')
        parser.add_argument('--dry-run', '-d', action='store_true', required=False, help="Don't actually do anything")
        parser.add_argument('--config', '-c', type=str, required=False, default=config_file, help="Configuration file")
        parser.add_argument('file', nargs=1, help='Path to the new recording file')

        args = parser.parse_args()
        config_file = Path(args.config).absolute()

        if not config_file.exists():
            raise RuntimeError(f'Config not found: {config_file}')

        config = Config.from_toml_file(config_file)

        return FileMover(config, args.file[0], args.verbose, args.dry_run)

    def collect_files(self) -> list[Path]:
        file_paths = []
        base_path = Path(self.config.app.base_source_dir)

        for ext in self.config.app.file_extensions:
            for candidate in base_path.rglob(f'*{ext}'):
                if candidate.is_file():
                    file_paths.append(candidate.resolve())

        return file_paths

    def get_target_path(self, path: Path) -> Path:
        file_date = parse(path.stem).date()

        year_str = f'{file_date.year:04}'
        month_str = f'{file_date.month:02}'
        day_str = f'{file_date.day:02}'

        return Path(self.config.app.base_target_dir) / year_str / month_str / day_str / path.name

    def create_remote_path_if_missing(self, path: str):
        try:
            self.sftp_client.stat(path)
        except FileNotFoundError as e:
            self.log(f'Creating target path: {path}')

            if not self.dry_run:
                self.sftp_client.mkdir(path)

    def ensure_target_dir(self, path: Path):
        for parent in reversed(list(path.parents)):
            self.create_remote_path_if_missing(str(parent))

    def move_one_file(self, path: Path):
        target_host = self.config.ssh.host

        target_path = self.get_target_path(path)

        self.log(f'Copying "{path}" to "{target_host}:{target_path}"')
        self.ensure_target_dir(target_path)

        if self.dry_run:
            return

        cb = None
        if self.verbose:
            file_size = os.path.getsize(str(path))

            progress = tqdm(total=file_size, unit='B', unit_scale=True, desc="Uploading", file=sys.stdout)

            def callback(transferred, total):
                progress.n = transferred
                progress.refresh()
                if transferred == total:
                    progress.close()

            cb = callback

        self.sftp_client.put(str(path), str(target_path), callback=cb)

        self.log(f'Removing "{path}"')
        os.remove(str(path))

    def run(self):
        self.log(f'New recording: {self.new_file}')
        self.log(f'Source base:   {self.config.app.base_source_dir}')
        self.log(f'Target base:   {self.config.app.base_target_dir}')
        self.log(f'Extensions:    {self.config.app.file_extensions}')
        self.log(f'Dry run:       {self.dry_run}')

        files_to_move = self.collect_files()
        print(f'Files to move: {len(files_to_move)}')

        for path in files_to_move:
            if path == self.new_file:
                self.log(f'Skipping new recording: {path}')
                continue

            self.move_one_file(path)
