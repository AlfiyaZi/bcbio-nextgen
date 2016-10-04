from collections import namedtuple
import pytest
import mock

from bcbio.distributed import transaction
from bcbio.distributed.transaction import tx_tmpdir
from bcbio.distributed.transaction import file_transaction
from bcbio.distributed.transaction import _get_base_tmpdir
from bcbio.distributed.transaction import _get_config_tmpdir
from bcbio.distributed.transaction import _get_config_tmpdir_path
from bcbio.distributed.transaction import _dirs_to_remove
from bcbio.distributed.transaction import _flatten_plus_safe
from bcbio.distributed.transaction import _remove_tmpdirs
from bcbio.distributed.transaction import _remove_files
from bcbio.distributed.transaction import _move_file_with_sizecheck


CWD = 'TEST_CWD'
CONFIG = {'a': 1}
TMP = '/tmp'


class DummyCM(object):
    value = None

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def __getattr__(self, attr):
        return self.stuff.__getattribute__(attr)


class DummyTxTmpdir(DummyCM):
    stuff = 'foo'

    def __iadd__(self, other):
        return self.stuff + other


class DummyFlattenPlusSafe(DummyCM):
    value = (['foo'], ['bar'])

    def __iter__(self):
        for v in self.value:
            yield v


@pytest.yield_fixture
def mock_tx_tmpdir(mocker):
    yield mocker.patch(
        'bcbio.distributed.transaction.tx_tmpdir',
        side_effect=DummyTxTmpdir
    )


@pytest.yield_fixture
def mock_flatten(mocker):
    yield mocker.patch(
        'bcbio.distributed.transaction._flatten_plus_safe',
        side_effect=DummyFlattenPlusSafe
    )


@pytest.yield_fixture
def mock_io(mocker):
    mocker.patch('bcbio.distributed.transaction.shutil')
    mocker.patch('bcbio.distributed.transaction.os.remove')
    mocker.patch('bcbio.distributed.transaction.os.rename')
    mocker.patch('bcbio.distributed.transaction.utils.safe_makedir')
    mocker.patch('bcbio.distributed.transaction.os.stat')
    mocker.patch('bcbio.distributed.transaction.tempfile')
    mocker.patch(
        'bcbio.distributed.transaction.os.getcwd',
        return_value=CWD
    )
    yield None


@pytest.yield_fixture
def mock_uuid(mocker):
    mocked = mocker.patch(
        'bcbio.distributed.transaction.uuid.uuid4',
        return_value='TESTUUID4'
    )
    yield mocked


@mock.patch('bcbio.distributed.transaction.os.path.exists')
def test_tx_tmpdir_make_tmp_dir(mock_exists, mock_io, mock_uuid):
    with tx_tmpdir():
        pass
    expected_basedir = "%s/bcbiotx/TESTUUID4" % TMP
    transaction.tempfile.mkdtemp.assert_called_once_with(
        dir=expected_basedir)
    transaction.utils.safe_makedir.assert_called_once_with(expected_basedir)


@mock.patch('bcbio.distributed.transaction.os.path.exists')
def test_tx_tmpdir_yields_tmp_dir(mock_exists, mock_io):
    expected = transaction.tempfile.mkdtemp.return_value
    with tx_tmpdir() as tmp_dir:
        assert tmp_dir == expected


@mock.patch('bcbio.distributed.transaction.os.path.exists')
@mock.patch('bcbio.distributed.transaction._get_base_tmpdir')
@mock.patch('bcbio.distributed.transaction._get_config_tmpdir')
@mock.patch('bcbio.distributed.transaction._get_config_tmpdir_path')
def test_tx_tmpdir_yields_created_dir(
        mock_get_config_tmpdir_path,
        mock_get_config_tmpdir,
        mock_get_base_tmpdir,
        mock_exists, mock_io):
    data, base_dir = mock.Mock(), mock.Mock()
    with tx_tmpdir(data, base_dir):
        pass
    mock_get_config_tmpdir.assert_called_once_with(data)
    mock_get_config_tmpdir_path.assert_called_once_with(
        mock_get_config_tmpdir.return_value, CWD)
    mock_get_base_tmpdir.assert_called_once_with(
        mock_get_config_tmpdir_path.return_value)

    transaction.utils.safe_makedir.assert_called_once_with(
        mock_get_base_tmpdir.return_value)
    transaction.tempfile.mkdtemp.assert_called_once_with(
        dir=mock_get_base_tmpdir.return_value)


@pytest.mark.parametrize(
    ('config_tmp', 'expected'), [
        ('/path/to/dir', '%s/bcbiotx/TESTUUID4' % '/path/to/dir'),
        (None, '%s/bcbiotx/TESTUUID4' % '/tmp'),
    ])
def test_get_base_tmpdir(config_tmp, expected, mock_uuid):
    result = _get_base_tmpdir(config_tmp)
    assert result == expected


def test_get_config_tmpdir__from_config():
    config = {
        'config': {
            'resources': {
                'tmp': {'dir': 'TEST_TMP_DIR'}
            }
        }
    }
    expected = 'TEST_TMP_DIR'
    result = _get_config_tmpdir(config)
    assert result == expected


def test_get_config_tmpdir__from_resources():
    config = {
        'resources': {
            'tmp': {'dir': 'TEST_TMP_DIR'}
        }
    }
    expected = 'TEST_TMP_DIR'
    result = _get_config_tmpdir(config)
    assert result == expected


def test_get_config_tmpdir__no_data():
    result = _get_config_tmpdir(None)
    assert result is None


def test_get_config_tmpdir_path():
    result = _get_config_tmpdir_path(None, 'whatever')
    assert result is None


@mock.patch('bcbio.distributed.transaction.os.path')
def test_get_config_tmpdir_path__flow(mock_path):
    TMP = 'TEST_CONFIG_TMP'

    mock_path.expandvars.return_value = 'EXPANDED'
    mock_path.join.return_value = 'JOINED'
    mock_path.normpath.return_value = 'NORMALIZED'

    result = _get_config_tmpdir_path(TMP, CWD)

    mock_path.expandvars.assert_called_once_with(TMP)
    mock_path.join.assert_called_once_with(CWD, 'EXPANDED')
    mock_path.normpath.assert_called_once_with('JOINED')

    assert result == 'NORMALIZED'


@mock.patch('bcbio.distributed.transaction.os.path.exists')
@mock.patch('bcbio.distributed.transaction._dirs_to_remove')
def test_tx_tmpdir_rmtree_not_called_if_remove_is_false(
        mock_dirs_to_remove, mock_exists, mock_io):
    mock_dirs_to_remove.return_value = ['foo']
    with tx_tmpdir(remove=False):
        pass
    assert not transaction.shutil.rmtree.called


@mock.patch('bcbio.distributed.transaction.os.path.exists')
@mock.patch('bcbio.distributed.transaction._dirs_to_remove')
def test_tx_tmpdir_rmtree_called_if_remove_is_True(
        mock_dirs_to_remove, mock_exists, mock_io):
    mock_dirs_to_remove.return_value = ['foo']
    with tx_tmpdir(remove=True):
        pass
    transaction.shutil.rmtree.assert_called_once_with(
        'foo', ignore_errors=True)


@pytest.mark.parametrize(
    ('tmp_dir', 'tmp_dir_base', 'config_tmpdir', 'expected'),
    [
        ('foo', 'bar', 'baz', ['foo', 'bar']),
        ('foo', 'bar', None, ['foo']),
        (None, None, 'baz', []),
        ('foo', None, 'baz', ['foo']),
        (None, 'bar', 'baz', ['bar']),
    ]
)
def test_get_dirs_to_remove(tmp_dir, tmp_dir_base, config_tmpdir, expected):
    result = _dirs_to_remove(tmp_dir, tmp_dir_base, config_tmpdir)
    assert list(result) == expected


@pytest.mark.parametrize(('args', 'exp_tx_args'), [
    (('/path/to/somefile',), (None,)),
    ((CONFIG, '/path/to/somefile'), (CONFIG,)),
    ((CONFIG, ['/path/to/somefile']), (CONFIG,)),
    ((CONFIG, '/path/to/somefile', '/otherpath/to/file'), (CONFIG,))
])
def test_flatten_plus_safe_calls_tx_tmpdir(args, exp_tx_args, mock_tx_tmpdir):
    with _flatten_plus_safe(args) as (result_tx, result_safe):
        pass
    mock_tx_tmpdir.assert_called_once_with(*exp_tx_args)


@pytest.mark.parametrize(('args', 'expected_tx'), [
    (('/path/to/somefile',), ['foo/somefile']),
    ((CONFIG, '/path/to/somefile'), ['foo/somefile']),
    ((CONFIG, ['/path/to/somefile']), ['foo/somefile']),
    (
        (CONFIG, '/path/to/somefile', '/otherpath/to/otherfile'),
        ['foo/somefile', 'foo/otherfile'],
    )]
)
def test_flatten_plus_safe_creates_tx_file_in_tmp_dir(
        args, expected_tx, mock_tx_tmpdir):
    with _flatten_plus_safe(args) as (result_tx, _):
        assert result_tx == expected_tx


@pytest.mark.parametrize(('args', 'expected_safe'), [
    (('/path/to/somefile',), ['/path/to/somefile']),
    ((CONFIG, '/path/to/somefile'), ['/path/to/somefile']),
    ((CONFIG, ['/path/to/somefile']), ['/path/to/somefile']),
    (
        (CONFIG, '/path/to/somefile', '/otherpath/to/otherfile'),
        ['/path/to/somefile', '/otherpath/to/otherfile'],
    )]
)
def test_flatten_plus_safe_returns_original_files(
        args, expected_safe, mock_tx_tmpdir):
    with _flatten_plus_safe(args) as (_, result_safe):
        assert result_safe == expected_safe


def test_flatten_plus_safe_doesnt_break_on_empty_paths(mock_tx_tmpdir):
    args = (CONFIG,)
    with _flatten_plus_safe(args) as (a, b):
        assert a == []
        assert b == []


@mock.patch('bcbio.distributed.transaction.os.path')
def test_remove_tmpdirs_removes_parent_directory(mock_path, mock_io):
    fnames = ['foo']
    mock_path.exists.return_value = True

    _remove_tmpdirs(fnames)
    mock_path.dirname.assert_called_once_with(
        mock_path.abspath.return_value)
    transaction.shutil.rmtree.assert_called_once_with(
        mock_path.dirname.return_value, ignore_errors=True)


@mock.patch('bcbio.distributed.transaction.os.path')
def test_remove_tmpdirs_doesnt_remove_par_dir_if_not_exists(
        mock_path, mock_io):
    fnames = ['foo']
    mock_path.exists.return_value = False

    _remove_tmpdirs(fnames)
    assert not transaction.shutil.rmtree.called


@mock.patch('bcbio.distributed.transaction.os.path')
def test_remove_tmpdirs_removes_pardir_of_each_file(mock_path, mock_io):
    fnames = mock.MagicMock(spec=list)
    mock_path.exists.return_value = False

    _remove_tmpdirs(fnames)
    assert fnames.__iter__.called


@mock.patch('bcbio.distributed.transaction.os.path')
def test_remove_files_with_os_remove(mock_path, mock_io):
    fnames = ['foo']
    mock_path.exists.return_value = True
    mock_path.isfile.return_value = True
    mock_path.isdir.return_value = False

    _remove_files(fnames)
    assert not transaction.shutil.rmtree.called
    assert transaction.os.remove.called


@mock.patch('bcbio.distributed.transaction.os.path')
def test_remove_files_removes_dirs_with_rmtree(mock_path, mock_io):
    fnames = ['foo']
    mock_path.exists.return_value = True
    mock_path.isfile.return_value = False
    mock_path.isdir.return_value = True

    _remove_files(fnames)
    assert transaction.shutil.rmtree.called
    assert not transaction.os.remove.called


@mock.patch('bcbio.distributed.transaction.os.path')
def test_remove_files_doesnt_remove_nonexistent_files(mock_path, mock_io):
    fnames = ['foo']
    mock_path.exists.return_value = False

    _remove_files(fnames)
    assert not transaction.shutil.rmtree.called
    assert not transaction.os.remove.called


@mock.patch('bcbio.distributed.transaction.os.path')
def test_remove_files_iterates_over_fnames(
        mock_path, mock_io):
    fnames = mock.MagicMock(spec=list)
    mock_path.exists.return_value = False

    _remove_files(fnames)
    assert fnames.__iter__.called


MockIO = namedtuple('MockIO', [
    'shutil', 'os_remove', 'os_rename', 'safe_makedir', 'os_stat', 'os_getcwd'
])


@mock.patch('bcbio.distributed.transaction.os.path')
def test_move_with_sizecheck(mock_path, mock_io):
    _move_file_with_sizecheck('foo', 'bar')
    transaction.shutil.move.assert_called_once_with('foo', 'bar')


def test_file_transaction(mock_io):
    # TODO extract meaning out of file-tansaction :)
    with file_transaction(CONFIG, '/some/path'):
        pass
