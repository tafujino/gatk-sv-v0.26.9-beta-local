ARG SAMTOOLS_CLOUD_IMAGE=samtools-cloud:latest
FROM $SAMTOOLS_CLOUD_IMAGE

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -qqy update --fix-missing && \
    apt-get -qqy dist-upgrade && \
    apt-get -qqy install --no-install-recommends \
                 bcftools \
                 gawk \
                 libgomp1 \
                 tabix \
                 zlib1g-dev && \
    apt-get -qqy autoremove --purge && \
    apt-get -qqy clean && \
    rm -rf /tmp/* \
           /var/tmp/* \
           /var/cache/apt/* \
           /var/lib/apt/lists/* \
           /usr/share/man/?? \
           /usr/share/man/??_*

COPY dockerfiles/wham/whamg /bin/
