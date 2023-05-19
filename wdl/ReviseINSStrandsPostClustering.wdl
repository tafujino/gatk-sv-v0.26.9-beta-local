version 1.0

import "Structs.wdl"

workflow ReviseINSStrandsPostClustering {
  input {
    File clustered_manta_vcf
    File clustered_melt_vcf

    String sv_pipeline_docker
    RuntimeAttr? runtime_attr_revise_ins_strands
  }

  Array[File] vcfs = [clustered_manta_vcf, clustered_melt_vcf]

  scatter (vcf in vcfs) {
    call ReviseINSStrands {
      input:
        vcf=vcf,
        sv_pipeline_docker=sv_pipeline_docker,
        runtime_attr_override=runtime_attr_revise_ins_strands
    }
  }

  output {
    File revised_manta_vcf = ReviseINSStrands.revised_vcf[0]
    File revised_manta_vcf_index = ReviseINSStrands.revised_vcf_index[0]
    File revised_melt_vcf = ReviseINSStrands.revised_vcf[1]
    File revised_melt_vcf_index = ReviseINSStrands.revised_vcf_index[1]
  }
}

task ReviseINSStrands {
  input {
    File vcf
    String sv_pipeline_docker
    RuntimeAttr? runtime_attr_override
  }

  String outfile = basename(vcf, ".vcf.gz") + ".revised.vcf.gz"

  RuntimeAttr default_attr = object {
                               cpu_cores: 1,
                               mem_gb: 3.75,
                               disk_gb: ceil(size(vcf, "GB") * 2 + 10),
                               boot_disk_gb: 10,
                               preemptible_tries: 3,
                               max_retries: 1
                             }
  RuntimeAttr runtime_attr = select_first([runtime_attr_override, default_attr])

  command <<<
    set -euo pipefail

    python3 <<CODE
    import pysam
    with pysam.VariantFile("~{vcf}", 'r') as f_in, pysam.VariantFile("~{outfile}", 'w', header=f_in.header) as f_out:
      for record in f_in:
        if record.info["SVTYPE"] == "INS":
          record.info["STRANDS"] = "-+"
        f_out.write(record)
    CODE
    tabix ~{outfile}
  >>>

  output {
    File revised_vcf = outfile
    File revised_vcf_index = "~{outfile}.tbi"
  }

  runtime {
    cpu: select_first([runtime_attr.cpu_cores, default_attr.cpu_cores])
    memory: select_first([runtime_attr.mem_gb, default_attr.mem_gb]) + " GiB"
    disks: "local-disk " + select_first([runtime_attr.disk_gb, default_attr.disk_gb]) + " HDD"
    bootDiskSizeGb: select_first([runtime_attr.boot_disk_gb, default_attr.boot_disk_gb])
    docker: sv_pipeline_docker
    preemptible: select_first([runtime_attr.preemptible_tries, default_attr.preemptible_tries])
    maxRetries: select_first([runtime_attr.max_retries, default_attr.max_retries])
  }
}
