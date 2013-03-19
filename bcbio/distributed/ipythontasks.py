"""Ipython parallel ready entry points for parallel execution
"""
import contextlib

from IPython.parallel import require

from bcbio.pipeline import sample, lane, qcsummary, shared, variation
from bcbio.variation import bamprep, realign, genotype, ensemble, multi, recalibrate
from bcbio.log import setup_logging, logger

@contextlib.contextmanager
def _setup_logging(args):
    if len(args) > 0:
        for check_i in [0, -1]:
            config = args[0][check_i]
            if isinstance(config, dict) and config.has_key("config"):
                config = config["config"]
                break
            elif isinstance(config, dict) and config.has_key("algorithm"):
                break
            else:
                config = None
        setup_logging(config)
    try:
        yield None
    except:
        logger.exception("Unexpected error")
        raise

@require(lane)
def process_lane(*args):
    with _setup_logging(args):
        return apply(lane.process_lane, *args)

@require(lane)
def trim_lane(*args):
    with _setup_logging(args):
        return apply(lane.trim_lane, *args)

@require(lane)
def process_alignment(*args):
    with _setup_logging(args):
        return apply(lane.process_alignment, *args)
process_alignment.metadata = {"resources": ["novoalign", "bwa"]}

@require(lane)
def align_prep_full(*args):
    with _setup_logging(args):
        return apply(lane.align_prep_full, *args)
align_prep_full.metadata = {"resources": ["novoalign", "bwa", "gatk"]}

@require(sample)
def merge_sample(*args):
    with _setup_logging(args):
        return apply(sample.merge_sample, *args)

@require(sample)
def delayed_bam_merge(*args):
    with _setup_logging(args):
        return apply(sample.delayed_bam_merge, *args)

@require(sample)
def recalibrate_sample(*args):
    with _setup_logging(args):
        return apply(sample.recalibrate_sample, *args)

@require(recalibrate)
def prep_recal(*args):
    with _setup_logging(args):
        return apply(recalibrate.prep_recal, *args)
prep_recal.metadata = {"resources": ["gatk"]}

@require(recalibrate)
def write_recal_bam(*args):
    with _setup_logging(args):
        return apply(recalibrate.write_recal_bam, *args)

@require(realign)
def realign_sample(*args):
    with _setup_logging(args):
        return apply(realign.realign_sample, *args)

@require(multi)
def split_variants_by_sample(*args):
    with _setup_logging(args):
        return apply(multi.split_variants_by_sample, *args)

@require(bamprep)
def piped_bamprep(*args):
    with _setup_logging(args):
        return apply(bamprep.piped_bamprep, *args)

@require(variation)
def postprocess_variants(*args):
    with _setup_logging(args):
        return apply(variation.postprocess_variants, *args)

@require(qcsummary)
def pipeline_summary(*args):
    with _setup_logging(args):
        return apply(qcsummary.pipeline_summary, *args)

@require(sample)
def generate_transcript_counts(*args):
    with _setup_logging(args):
        return apply(sample.generate_transcript_counts, *args)

@require(sample)
def generate_bigwig(*args):
    with _setup_logging(args):
        return apply(sample.generate_bigwig, *args)

@require(shared)
def combine_bam(*args):
    with _setup_logging(args):
        return apply(shared.combine_bam, *args)

@require(genotype)
def variantcall_sample(*args):
    with _setup_logging(args):
        return apply(genotype.variantcall_sample, *args)

@require(genotype)
def combine_variant_files(*args):
    with _setup_logging(args):
        return apply(genotype.combine_variant_files, *args)

@require(variation)
def detect_sv(*args):
    with _setup_logging(args):
        return apply(variation.detect_sv, *args)

@require(ensemble)
def combine_calls(*args):
    with _setup_logging(args):
        return apply(ensemble.combine_calls, *args)
