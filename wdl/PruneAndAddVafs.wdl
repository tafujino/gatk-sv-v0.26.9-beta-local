# Workflow to perform final sample pruning & compute all relevant AF statistics
# for a VCF from the Talkowski SV pipeline

version 1.0

import "TasksMakeCohortVcf.wdl" as MiniTasks
import "Utils.wdl" as util

# Prune off samples in annotated VCF, add VAF annotation
workflow PruneAndAddVafs {
  
  input {

    File vcf
    File vcf_idx
    String prefix
    String contig

    File? sample_pop_assignments  # Two-column file with sample ID & pop assignment. "." for pop will ignore sample
    File? ped_file                # Used for M/F AF calculations
    File? par_bed
    File? allosomes_list
    File? sample_keep_list              # List of samples to be retained from the output vcf

    String sv_base_mini_docker
    String sv_pipeline_docker

    RuntimeAttr? runtime_attr_compute_AFs
    RuntimeAttr? runtime_attr_subset_vcf_by_samples_list
  }
  
  # Prune VCF
  if (defined(sample_keep_list)) {
    call util.SubsetVcfBySamplesList {
      input:
        vcf = vcf,
        vcf_idx = vcf_idx,
        list_of_samples = select_first([sample_keep_list]),
        sv_base_mini_docker = sv_base_mini_docker,
        runtime_attr_override = runtime_attr_subset_vcf_by_samples_list
    }
  }

  # Compute AC, AN, and AF per population & sex combination
  call ComputeShardAFs {
    input:
      vcf = select_first([SubsetVcfBySamplesList.vcf_subset, vcf]),
      prefix = prefix,
      sample_pop_assignments = sample_pop_assignments,
      ped_file = ped_file,
      par_bed = par_bed,
      allosomes_list = allosomes_list,
      sv_pipeline_docker = sv_pipeline_docker,
      runtime_attr_override = runtime_attr_compute_AFs
  }

  output {
    File output_vcf = ComputeShardAFs.shard_wAFs
    File output_vcf_idx = ComputeShardAFs.shard_wAFs_idx
  }
}

