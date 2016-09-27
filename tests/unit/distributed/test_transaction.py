import pytest
import mock

from bcbio.distributed.transaction import tx_tmpdir



@mock.patch('bcbio.distributed.transaction.shutil')
@mock.patch('bcbio.distributed.transaction.tempfile')
@mock.patch('bcbio.distributed.transaction.utils.safe_makedir')
@mock.patch('bcbio.distributed.transaction.os.path')
@mock.patch('bcbio.distributed.transaction.os.getcwd')
def test_tx_tmpdir(
        mock_getcwd, mock_path,  mock_utils, mock_tempfile, mock_shutil):
    mock_path.exists.return_value = False
    mock_getcwd.return_value = "test_cwd"
    with tx_tmpdir():
        pass
    assert mock_utils.call_count == 2


@mock.patch('bcbio.distributed.transaction.shutil')
@mock.patch('bcbio.distributed.transaction.tempfile')
@mock.patch('bcbio.distributed.transaction.utils.safe_makedir')
@mock.patch('bcbio.distributed.transaction.os')
def test_get_config_tmpdir(
        mock_os,  mock_utils, mock_tempfile, mock_shutil):
    mock_os.path.exists.return_value = False
    config = {
        'config': {
            'resources': {
                'tmp': {'dir': 'TEST_TMP_DIR'}
            }
        }
    }
    with tx_tmpdir(data=config):
        pass
    mock_os.path.expandvars.assert_called_once_with('TEST_TMP_DIR')


@mock.patch('bcbio.distributed.transaction.shutil')
@mock.patch('bcbio.distributed.transaction.tempfile')
@mock.patch('bcbio.distributed.transaction.utils.safe_makedir')
@mock.patch('bcbio.distributed.transaction.os')
def test_get_resources_tmpdir(
        mock_os,  mock_utils, mock_tempfile, mock_shutil):
    mock_os.path.exists.return_value = False
    config = {
        'resources': {
            'tmp': {'dir': 'TEST_TMP_DIR'}
        }
    }
    with tx_tmpdir(data=config):
        pass
    mock_os.path.expandvars.assert_called_once_with('TEST_TMP_DIR')


@mock.patch('bcbio.distributed.transaction.shutil')
@mock.patch('bcbio.distributed.transaction.tempfile')
@mock.patch('bcbio.distributed.transaction.utils.safe_makedir')
@mock.patch('bcbio.distributed.transaction.os')
def test_gets_tmp_dir_from_config_over_resources(
        mock_os,  mock_utils, mock_tempfile, mock_shutil):
    mock_os.path.exists.return_value = False
    config = {
        'resources': {
            'tmp': {'dir': 'TMP_RESOURCES'}
        },
        'config': {
            'resources': {
                'tmp': {'dir': 'TMP_CONFIG'}
            }
        }
    }
    with tx_tmpdir(data=config):
        pass
    mock_os.path.expandvars.assert_called_once_with('TMP_CONFIG')


