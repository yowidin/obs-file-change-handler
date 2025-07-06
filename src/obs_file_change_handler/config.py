from pathlib import Path, PurePosixPath
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, FilePath, DirectoryPath, AfterValidator
from annotated_types import MinLen, Interval

import tomlkit

# A file extension starts with '.', consists of words and digits and can be anywhere between 1 and 6 characters long
type FileExtension = Annotated[str, StringConstraints(pattern=r'^\.(?:\w|\d){1,6}$')]

type NonEmptyList = Annotated[list, MinLen(1)]
type NonEmptyString = Annotated[str, MinLen(1)]


class SSHConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: NonEmptyString
    port: Annotated[int, Interval(gt=0, le=65535)] = 22
    username: NonEmptyString
    password: NonEmptyString | None = None
    private_key: FilePath | None = None


def validate_target_dir(v: str) -> str:
    tmp = PurePosixPath(v)
    if not tmp.is_absolute():
        raise ValueError('Path must be absolute (start with /)')
    return v


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Base directory on the target machine.
    # All the files will be further organized by date inside the base directory, for example:
    # ${base_target_dir}/2025/06/30/2025-06-30 15-32-04.mp4
    base_target_dir: Annotated[str, AfterValidator(validate_target_dir)]

    # Base directory on the source machine.
    # All files with the matching file extensions will be moved from that base directory (and all subdirectories) onto
    # the target machine.
    base_source_dir: DirectoryPath

    file_extensions: Annotated[list[FileExtension], MinLen(1)]


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ssh: SSHConfig
    app: AppConfig

    @staticmethod
    def from_toml_file(path: Path) -> 'Config':
        file_contents = path.read_text()
        as_toml = tomlkit.loads(file_contents)
        as_dict = as_toml.unwrap()
        result = Config.model_validate(as_dict)
        if not result.app.base_target_dir.startswith('/'):
            raise RuntimeError(f"Target dir must be absolute")
        return result
