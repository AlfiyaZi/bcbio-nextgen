"""Handle file based transactions allowing safe restarts at any point.

To handle interrupts,this defines output files written to temporary
locations during processing and copied to the final location when finished.
This ensures output files will be complete independent of method of
interruption.
"""
import contextlib
import os
import shutil
import tempfile

import toolz as tz

from bcbio import utils
from bcbio.log import logger


DEFAULT_TMP = '/tmp/bcbiotx'


@contextlib.contextmanager
def tx_tmpdir(data=None, remove=True):
    """Context manager to create and remove a transactional temporary directory.

    Handles creating a transactional directory for running commands in. Will
    use either the current directory or /tmp/bcbiotx.

    Creates an intermediary location and time specific directory for global
    temporary directories to prevent collisions.

    data can be the full world information object being process or a
    configuration dictionary.
    """
    cwd = os.getcwd()
    tmpdir_base = _get_base_tmpdir(data)
    tmpdir_base = _get_dir_abspath(tmpdir_base, cwd)

    utils.safe_makedir(tmpdir_base)
    tmp_dir = tempfile.mkdtemp(dir=tmpdir_base)
    logger.info("Created tmp dir %s " % tmp_dir)
    try:
        yield tmp_dir
    finally:
        if remove:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _get_dir_abspath(path, default_pardir):
    path = os.path.expandvars(path)
    return os.path.normpath(os.path.join(default_pardir, path))


def _get_base_tmpdir(data):
    config_tmpdir = tz.get_in(("config", "resources", "tmp", "dir"), data)
    if not config_tmpdir:
        config_tmpdir = tz.get_in(("resources", "tmp", "dir"), data)
    return config_tmpdir or DEFAULT_TMP


@contextlib.contextmanager
def file_transaction(*data_and_files):
    """Wrap file generation in a transaction, moving to output if finishes.

    The initial argument can be the world descriptive `data` dictionary, or
    a `config` dictionary. This is used to identify global settings for
    temporary directories to create transactional files in.
    """
    with _flatten_plus_safe(data_and_files) as (safe_names, orig_names):
        _remove_files(safe_names)  # remove any half-finished transactions
        # no need for try except block here,
        # because exceptions and tmp dir removal
        # are handled by tx_tmpdir contextmanager
        if len(safe_names) == 1:
            yield safe_names[0]
        else:
            yield tuple(safe_names)

        for safe, orig in zip(safe_names, orig_names):
            if os.path.exists(safe):
                _move_tmp_files(safe, orig)


def _move_tmp_files(safe, orig):
    exts = {
        ".vcf": ".idx",
        ".bam": ".bai",
        ".vcf.gz": ".tbi",
        ".bed.gz": ".tbi"
    }

    utils.safe_makedir(os.path.dirname(orig))
    # If we are rolling back a directory and it already exists
    # this will avoid making a nested set of directories
    if os.path.isdir(orig) and os.path.isdir(safe):
        shutil.rmtree(orig)

    _move_file_with_sizecheck(safe, orig)
    # Move additional, associated files in the same manner
    for check_ext, check_idx in exts.iteritems():
        if not safe.endswith(check_ext):
            continue
        safe_idx = safe + check_idx
        if os.path.exists(safe_idx):
            _move_file_with_sizecheck(safe_idx, orig + check_idx)


def _move_file_with_sizecheck(tx_file, final_file):
    """Move transaction file to final location,
       with size checks avoiding failed transfers.
    """

    logger.debug("Moving %s to %s" % (tx_file, final_file))
    # Remove any partially transferred directories or files
    if os.path.exists(final_file):
        _remove_files([final_file])

    want_size = utils.get_size(tx_file)
    # Move files from temporary storage to shared storage
    shutil.move(tx_file, final_file)

    # Validate that file sizes of file before and after transfer are identical
    try:
        transfer_size = utils.get_size(final_file)
    # Avoid race conditions where transaction file has already been renamed
    except OSError as e:
        logger.debug("Error when moving a tmp file: %s" % str(e))
        return
    assert want_size == transfer_size, (
        'distributed.transaction.file_transaction: File copy error: '
        'file or directory on temporary storage ({}) size {} bytes '
        'does not equal size of file or directory after transfer to '
        'shared storage ({}) size {} bytes'.format(
            tx_file, want_size, final_file, transfer_size)
    )


def _remove_files(fnames):
    for x in fnames:
        if x and os.path.exists(x):
            if os.path.isfile(x):
                os.remove(x)
            elif os.path.isdir(x):
                shutil.rmtree(x, ignore_errors=True)


@contextlib.contextmanager
def _flatten_plus_safe(data_and_files):
    """Flatten names of files and create temporary file names.
    """
    data, rollback_files = _normalize_args(data_and_files)
    with tx_tmpdir(data) as tmpdir:
        tx_files = [os.path.join(tmpdir, os.path.basename(f))
                    for f in rollback_files]
        yield tx_files, rollback_files


def _normalize_args(data_and_files):
    data, files = _get_args(data_and_files)
    rollback_files = [f for f in _flatten(files) if f]
    return (data, rollback_files)


def _get_args(data_and_files):
    if isinstance(data_and_files[0], dict):
        return data_and_files[0], data_and_files[1:]
    return None, data_and_files


def _flatten(iterable):
    for elem in iterable:
        if isinstance(elem, (tuple, list)):
            for i in elem:
                yield i
        else:
            yield elem
