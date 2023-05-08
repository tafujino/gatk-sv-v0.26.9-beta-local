version 1.0

import "Structs.wdl"
import "TasksMakeCohortVcf.wdl" as MiniTasks
import "HailMerge.wdl" as HailMerge
import "AnnotateFunctionalConsequences.wdl" as func
import "PruneAndAddVafs.wdl" as pav
import "AnnotateExternalAF.wdl" as eaf

workflow ShardedAnnotateVcf {

  input {
    File vcf
    File vcf_idx
    String prefix
    String contig

    File protein_coding_gtf
    File? noncoding_bed
    Int? promoter_window
    Int? max_breakend_as_cnv_length
    String? svannotate_additional_args

    Int max_shards_per_chrom_step1
    Int min_records_per_shard_step1

    File? sample_pop_assignments  # Two-column file with sample ID & pop assignment. "." for pop will ignore sample
    File? sample_keep_list
    File? ped_file                # Used for M/F AF calculations
    File? par_bed
    File? allosomes_list
    Int   sv_per_shard

    File? ref_bed              # File with external allele frequencies
    String? ref_prefix         # prefix name for external AF call set (required if ref_bed set)
    Array[String]? population  # populations to annotate external AF for (required if ref_bed set)

    Boolean use_hail
    String? gcs_project

    String sv_pipeline_docker
    String? sv_pipeline_hail_docker
    String sv_base_mini_docker
    String gatk_docker

    RuntimeAttr? runtime_attr_svannotate
    RuntimeAttr? runtime_attr_compute_AFs
    RuntimeAttr? runtime_attr_subset_vcf_by_samples_list
    RuntimeAttr? runtime_attr_combine_vcfs
    RuntimeAttr? runtime_attr_modify_vcf
    RuntimeAttr? runtime_attr_combine_vcfs
    RuntimeAttr? runtime_attr_split_vcf
    RuntimeAttr? runtime_attr_split_ref_bed
    RuntimeAttr? runtime_attr_split_query_vcf
    RuntimeAttr? runtime_attr_bedtools_closest
    RuntimeAttr? runtime_attr_select_matched_svs
    RuntimeAttr? runtime_attr_scatter_vcf
    RuntimeAttr? runtime_attr_fix_ends_rescale_GQ
    RuntimeAttr? runtime_attr_concat_sharded_cluster
    RuntimeAttr? runtime_attr_preconcat_sharded_cluster
    RuntimeAttr? runtime_attr_hail_merge_sharded_cluster
    RuntimeAttr? runtime_attr_fix_header_sharded_cluster
  }

  call MiniTasks.ScatterVcf {
    input:
      vcf = vcf,
      prefix = prefix,
      records_per_shard = sv_per_shard,
      contig = contig,
      sv_pipeline_docker = sv_pipeline_docker,
      runtime_attr_override = runtime_attr_scatter_vcf
  }

  scatter (i in range(length(ScatterVcf.shards))) {

    call func.AnnotateFunctionalConsequences {
      input:
        vcf = ScatterVcf.shards[i],
        prefix = "~{prefix}.~{contig}.~{i}",
        protein_coding_gtf = protein_coding_gtf,
        noncoding_bed = noncoding_bed,
        promoter_window = promoter_window,
        max_breakend_as_cnv_length = max_breakend_as_cnv_length,
        additional_args = svannotate_additional_args,
        gatk_docker = gatk_docker,
        runtime_attr_svannotate = runtime_attr_svannotate
    }

    call pav.PruneAndAddVafs as PruneAndAddVafs {
      input:
        vcf = AnnotateFunctionalConsequences.annotated_vcf,
        vcf_idx = AnnotateFunctionalConsequences.annotated_vcf_index,
        prefix = "~{prefix}.~{contig}.~{i}",
        contig = contig,
        ped_file = ped_file,
        par_bed = par_bed,
        sample_keep_list = sample_keep_list,
        allosomes_list = allosomes_list,
        sample_pop_assignments = sample_pop_assignments,

        sv_base_mini_docker = sv_base_mini_docker,
        sv_pipeline_docker = sv_pipeline_docker,
        runtime_attr_subset_vcf_by_samples_list = runtime_attr_subset_vcf_by_samples_list,
        runtime_attr_compute_AFs = runtime_attr_compute_AFs,
    }

    if (defined(ref_bed)) {
      call eaf.AnnotateExternalAF as AnnotateExternalAF {
        input:
          vcf = PruneAndAddVafs.output_vcf,
          vcf_idx = PruneAndAddVafs.output_vcf_idx,
          ref_bed = select_first([ref_bed]),
          population = select_first([population]),
          ref_prefix = select_first([ref_prefix]),
          prefix = "~{prefix}.~{contig}.~{i}",
          contigs = [contig],
          max_shards_per_chrom_step1 = max_shards_per_chrom_step1,
          min_records_per_shard_step1 = min_records_per_shard_step1,
          sv_base_mini_docker = sv_base_mini_docker,
          sv_pipeline_docker = sv_pipeline_docker,
          runtime_attr_modify_vcf = runtime_attr_modify_vcf,
          runtime_attr_split_vcf = runtime_attr_split_vcf,
          runtime_attr_combine_vcfs = runtime_attr_combine_vcfs,
          runtime_attr_split_ref_bed = runtime_attr_split_ref_bed,
          runtime_attr_split_query_vcf = runtime_attr_split_query_vcf,
          runtime_attr_bedtools_closest = runtime_attr_bedtools_closest,
          runtime_attr_select_matched_svs = runtime_attr_select_matched_svs
      }
    }
  }

  output {
    Array[File] sharded_annotated_vcf = select_first([select_all(AnnotateExternalAF.annotated_vcf), PruneAndAddVafs.output_vcf])
    Array[File] sharded_annotated_vcf_idx = select_first([select_all(AnnotateExternalAF.annotated_vcf_tbi), PruneAndAddVafs.output_vcf_idx])
  }
}
