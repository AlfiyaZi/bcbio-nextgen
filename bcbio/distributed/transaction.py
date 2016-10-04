"""Handle file based transactions allowing safe restarts at any point.

To handle interrupts,this defines output files written to temporary
locations during processing and copied to the final location when finished.
This ensures output files will be complete independent of method of
interruption.
"""
import contextlib
import os
import uuid
import shutil
import tempfile

import toolz as tz

from bcbio import utils
from bcbio.log import logger


DEFAULT_TMP = '/tmp'


@contextlib.contextmanager
def tx_tmpdir(data=None, base_dir=None, remove=True):
    """Context manager to create and remove a transactional temporary directory.

    Handles creating a transactional directory for running commands in. Will
    use either the current directory or a configured temporary directory.

    Creates an intermediary location and time specific directory for global
    temporary directories to prevent collisions.

    data can be the full world information object being process or a
    configuration dictionary.
    """
    cwd = os.getcwd()
    config_tmpdir = _get_config_tmpdir(data)
    config_tmpdir_path = _get_config_tmpdir_path(config_tmpdir, cwd)
    tmp_dir_base = _get_base_tmpdir(config_tmpdir_path)

    utils.safe_makedir(tmp_dir_base)
    tmp_dir = tempfile.mkdtemp(dir=tmp_dir_base)
    logger.info("Created tmp dir %s " % tmp_dir)
    try:
        yield tmp_dir
    finally:
        if not remove:
            return
        for dname in _dirs_to_remove(tmp_dir, tmp_dir_base, config_tmpdir):
            shutil.rmtree(dname, ignore_errors=True)


def _get_config_tmpdir(data):
    config_tmpdir = None
    if data and "config" in data:
        config_tmpdir = tz.get_in(("config", "resources", "tmp", "dir"), data)
    elif data:
        config_tmpdir = tz.get_in(("resources", "tmp", "dir"), data)

    return config_tmpdir


def _get_config_tmpdir_path(config_tmpdir, cwd):
    if config_tmpdir:
        config_tmpdir = os.path.expandvars(config_tmpdir)
        config_tmpdir = os.path.normpath(os.path.join(cwd, config_tmpdir))

        return config_tmpdir
    return None


def _get_base_tmpdir(config_tmpdir):
    base = config_tmpdir if config_tmpdir else DEFAULT_TMP
    return os.path.join(base, "bcbiotx", str(uuid.uuid4()))


def _dirs_to_remove(tmp_dir, tmp_dir_base, config_tmpdir):
    result = (tmp_dir,)
    if config_tmpdir:
        result += (tmp_dir_base, )
    return (dirname for dirname in result if dirname)


@contextlib.contextmanager
def file_transaction(*data_and_files):
    """Wrap file generation in a transaction, moving to output if finishes.

    The initial argument can be the world descriptive `data` dictionary, or
    a `config` dictionary. This is used to identify global settings for
    temporary directories to create transactional files in.
    """
    with _flatten_plus_safe(data_and_files) as (safe_names, orig_names):
        # TODO  how can there be files with the same name if every
        # temporary dir has a unique name?
        _remove_files(safe_names)  # remove any half-finished transactions
        try:
            if len(safe_names) == 1:
                yield safe_names[0]
            else:
                yield tuple(safe_names)
        except Exception:  # failure -- delete any temporary files
            # TODO what determines if they are files or directories?
            _remove_files(safe_names)
            _remove_tmpdirs(safe_names)
            raise
        else:  # worked -- move the temporary files to permanent location
            for safe, orig in zip(safe_names, orig_names):
                if not os.path.exists(safe):
                    continue
                _move_tmp_files(safe, orig)
            _remove_tmpdirs(safe_names)


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


def _tx_size(orig):
    """Retrieve transactional size of a file or directory.
    """
    if os.path.isdir(orig):
        return sum([os.path.getsize(os.path.join(d, f))
                    for (d, _, filenames) in os.walk(orig)
                    for f in filenames])
    else:
        return os.path.getsize(orig)


def _move_file_with_sizecheck(tx_file, final_file):
    """Move transaction file to final location, with size checks avoiding failed transfers.
    """

    logger.info("Moving %s to %s" % (tx_file, final_file))
    tmp_file = final_file + ".bcbiotmp"
    # Remove any partially transferred directories or files
    if os.path.exists(final_file):
        if os.path.isdir(final_file):
            _remove_tmpdirs([final_file])
        else:
            _remove_files([final_file])
    want_size = _tx_size(tx_file)
    # Move files from temporary storage to shared storage under a temporary name
    shutil.move(tx_file, final_file)

    # Validate that file sizes of file before and after transfer are identical
    try:
        transfer_size = _tx_size(final_file)
    # Avoid race conditions where transaction file has already been renamed
    except OSError as e:
        logger.info( str(e))
        return
    assert want_size == transfer_size, \
        ('distributed.transaction.file_transaction: File copy error: '
         'file or directory on temporary storage ({}) size {} bytes '
         'does not equal size of file or directory after transfer to '
         'shared storage ({}) size {} bytes'.format(tx_file, want_size, final_file, transfer_size))
    # Atomically move temporary file on shared storage to final file on shared storage
    # os.rename(tmp_file, final_file)


def _remove_tmpdirs(fnames):
    for x in fnames:
        xdir = os.path.dirname(os.path.abspath(x))
        if xdir and os.path.exists(xdir):
            shutil.rmtree(xdir, ignore_errors=True)


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
    data_and_files = [x for x in data_and_files if x]
    if isinstance(data_and_files[0], dict):
        data = data_and_files[0]
        rollback_files = data_and_files[1:]
    else:
        data = None
        rollback_files = data_and_files
    tx_files, orig_files = [], []
    base_fname = rollback_files[0]
    if isinstance(base_fname, (list, tuple)):
        base_fname = base_fname[0]
    with tx_tmpdir(data, os.path.dirname(base_fname)) as tmpdir:
        for fnames in rollback_files:
            if isinstance(fnames, basestring):
                fnames = [fnames]
            for fname in fnames:
                tx_file = os.path.join(tmpdir, os.path.basename(fname))
                tx_files.append(tx_file)
                orig_files.append(fname)
        yield tx_files, orig_files
