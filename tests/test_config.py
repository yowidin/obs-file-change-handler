import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

from pydantic import ValidationError

from obs_file_change_handler.config import AppConfig, SSHConfig, Config


def test_ssh_config_fails_on_empty_user_name():
    with pytest.raises(ValidationError):
        _ = SSHConfig(host='localhost', username='')


def test_ssh_config_works_on_happy_path():
    direct = SSHConfig(host='localhost', username='user')
    as_json = """{"host":"localhost","port":22,"username":"user"}"""
    from_json = SSHConfig.model_validate_json(as_json)
    assert direct == from_json


def test_app_config_fails_on_empty_base_dir():
    with pytest.raises(ValidationError):
        _ = AppConfig(base_target_dir='', base_source_dir='/', file_extensions=['.mkv'])

    with pytest.raises(ValidationError):
        _ = AppConfig(base_target_dir='/', base_source_dir=' ', file_extensions=['.mkv'])


def test_app_config_fails_on_empty_extensions_list():
    with pytest.raises(ValidationError):
        _ = AppConfig(base_target_dir='/', base_source_dir='/', file_extensions=[])


def test_app_config_fails_on_invalid_extension():
    with pytest.raises(ValidationError):
        _ = AppConfig(base_target_dir='/', base_source_dir='/', file_extensions=['mkv'])


def test_app_config_fails_on_non_absolute_path():
    with pytest.raises(ValidationError):
        _ = AppConfig(base_target_dir='~/test', base_source_dir='/', file_extensions=['.mkv'])


def test_app_config_fails_with_extra_args():
    as_json = """{"base_target_dir":"/","base_source_dir":"/","file_extensions":[".mkv"],"foo":10}"""
    with pytest.raises(ValidationError):
        _ = AppConfig.model_validate_json(as_json)


def test_app_config_works_on_happy_path():
    direct = AppConfig(base_target_dir='/', base_source_dir='/', file_extensions=['.mkv', '.mp4', '.mov', '.avi'])
    as_json = """{"base_target_dir":"/","base_source_dir":"/","file_extensions":[".mkv",".mp4",".mov",".avi"]}"""
    from_json = AppConfig.model_validate_json(as_json)
    assert direct == from_json


def test_config_works_on_happy_path():
    with NamedTemporaryFile(mode='w', delete_on_close=False) as f:
        f.write(f"""
[app]
base_target_dir="/"
base_source_dir="/"
file_extensions=[".mkv"]

[ssh]
host="localhost"
username="user"
port=23
private_key='''{f.name}'''
"""
                )
        f.close()
        path = Path(f.name)
        from_toml = Config.from_toml_file(path)

        direct = Config(ssh=SSHConfig(host='localhost', port=23, username="user", private_key=path),
                        app=AppConfig(base_target_dir='/', base_source_dir='/', file_extensions=['.mkv']))
        assert direct == from_toml
