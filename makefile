#
# Starting in 5.2, the Jenkins builds for RM, core, etc expect the
# variables VERSION, SHORT_VERSION, hbase_VERSION, hdfs_VERSION, and
# opentsdb_VERSION to be defined by calling script defined in the
# zenoss/product-assembly repo.
#
# FIXME: Revisit the idea of using default values for these 5 variables
#        once we've resolved the build use-case for local developer builds.
#        The problem with the default values is that they repeat information
#        also recorded in the zenoss/product-assembly repo.
#

space := $(subst ,, )
# Local environment information
DOCKER = $(shell which docker)
PWD    = ${CURDIR}
UID    = $(shell id -u)
GID    = $(shell id -g)

# VERSION is the full Zenoss version; e.g., 5.0.0
# SHORT_VERSION is the two-digit Zenoss version; e.g., 5.0
# Note: these values are set in the build jobs, so the defaults =? aren't going to be used.
VERSION         ?= 7.1.0
SHORT_VERSION   = $(subst $(space),.,$(wordlist 1,2,$(subst ., ,$(VERSION))))

# These three xyz_VERSION variables define the corresponding docker image versions
hbase_VERSION    ?= 24.0.8
hdfs_VERSION     ?= 24.0.8
opentsdb_VERSION ?= 24.0.8
zing_connector_VERSION ?= latest
zing_api_proxy_VERSION ?= latest
otsdb_bigtable_VERSION ?= v3
impact_VERSION ?= 5.5.3.0.0

#
# Latch in the date with an immediate assignment to avoid
# date roll-over edge case incurred by lazy evaluation.
#
BUILD_NUMBER     ?= $(shell date +%Y%m%d%H%M%S)
_BUILD_NUMBER    := $(BUILD_NUMBER)
BUILD_IMAGE      ?= "zenoss/svcdefbuild"
BUILD_TYPE       ?= core
BUILD_NAME       ?= zenoss_$(BUILD_TYPE)-$(VERSION)
PREFIX           ?= /opt/zenoss
OUTPUT           ?= $(PWD)/output
MILESTONE        ?= unstable # unstable | testing | stable
MILESTONE_SUFFIX  =
RELEASE_PHASE    ?= # eg, BETA2 | ALPHA1 | CR13 | 1 | 2 | <blank>
_RELEASE_PHASE   := $(strip $(RELEASE_PHASE))

# Allow milestone to influence our artifact versioning.
BUILD_TAG      = $($(strip $(MILESTONE))_TAG)
stable_TAG     = $(VERSION)_$(_RELEASE_PHASE)
testing_TAG    = $(VERSION)_$(_RELEASE_PHASE)
unstable_TAG   = $(VERSION)_$(_BUILD_NUMBER)

# Suck in reference to an image
IMAGE_NUMBER        ?= $(_BUILD_NUMBER)
IMAGE_TAG            = $($(strip $(MILESTONE))_IMAGE_TAG)
stable_IMAGE_TAG     = $(VERSION)_$(_RELEASE_PHASE)
testing_IMAGE_TAG    = $(VERSION)_$(_RELEASE_PHASE)
unstable_IMAGE_TAG   = $(VERSION)_$(IMAGE_NUMBER)_unstable

# Describe docker repositories where we push entitled content.
repo_name_suffix      := _$(SHORT_VERSION)

image_REGPATH     =
image_PROJECT     = zenoss
image_core_REPO   = core$(repo_name_suffix)
image_core_REPO   = core$(repo_name_suffix)
image_cse_REPO    = cse$(repo_name_suffix)
image_SUFFIX      = $(MILESTONE_SUFFIX)

# Mechanism for overriding ImageIDs in service definition json source:
#
# from: ImageID: "zenoss/zenoss5x"
# into: ImageID: "zenoss/core_5.1:5.1.1_78_unstable"
#

jsonsrc_zenoss_ImageID = zenoss/zenoss5x
desired_zenoss_ImageID = gcr.io/zing-registry-188222/$(image_$(short_product)_REPO)$(image_SUFFIX):$(IMAGE_TAG)
svcdef_ImageID_maps   += $(jsonsrc_zenoss_ImageID),$(desired_zenoss_ImageID)

#
# Allow json to be updated automatically at build time if we switch publish
# repos in the makefile.
#
# NB: jsonsrc_<prod>_ImageID = what is currently in the source code.
#     desired_<prod>_ImageID = what you want the ID to be
#
jsonsrc_hbase_ImageID = zenoss/hbase:xx
desired_hbase_ImageID = $(image_PROJECT)/hbase:$(hbase_VERSION)
svcdef_ImageID_maps  += $(jsonsrc_hbase_ImageID),$(desired_hbase_ImageID)
#
jsonsrc_hdfs_ImageID = zenoss/hdfs:xx
desired_hdfs_ImageID = $(image_PROJECT)/hdfs:$(hdfs_VERSION)
svcdef_ImageID_maps  += $(jsonsrc_hdfs_ImageID),$(desired_hdfs_ImageID)
#
jsonsrc_opentsdb_ImageID = zenoss/opentsdb:xx
desired_opentsdb_ImageID = $(image_PROJECT)/opentsdb:$(opentsdb_VERSION)
svcdef_ImageID_maps     += $(jsonsrc_opentsdb_ImageID),$(desired_opentsdb_ImageID)
#
jsonsrc_zing_connector_ImageID = gcr-repo/zing-connector:xx
desired_zing_connector_ImageID = gcr.io/zing-registry-188222/zing-connector:$(zing_connector_VERSION)
svcdef_ImageID_maps     += $(jsonsrc_zing_connector_ImageID),$(desired_zing_connector_ImageID)
#
jsonsrc_zing_api_proxy_ImageID = gcr-repo/api-key-proxy:xx
desired_zing_api_proxy_ImageID = gcr.io/zing-registry-188222/api-key-proxy:$(zing_api_proxy_VERSION)
svcdef_ImageID_maps     += $(jsonsrc_zing_api_proxy_ImageID),$(desired_zing_api_proxy_ImageID)
#
jsonsrc_otsdb_bigtable_ImageID = zenoss/opentsdb-bigtable:xx
desired_otsdb_bigtable_ImageID = gcr.io/zing-registry-188222/otsdb-bigtable:$(otsdb_bigtable_VERSION)
svcdef_ImageID_maps     += $(jsonsrc_otsdb_bigtable_ImageID),$(desired_otsdb_bigtable_ImageID)
#
jsonsrc_impact_ImageID = zendev/impact-devimg
impact_folder = impact_$(shell echo $(impact_VERSION) | sed -E 's/([0-9]+).([0-9]+).*/\1.\2/')
desired_impact_ImageID = gcr.io/zing-registry-188222/$(impact_folder):$(impact_VERSION)
svcdef_ImageID_maps += $(jsonsrc_impact_ImageID),$(desired_impact_ImageID)
#
jsonsrc_mariadb_ImageID = zenoss/mariadb:xx
desired_mariadb_ImageID = gcr.io/zing-registry-188222/mariadb:$(IMAGE_TAG)
svcdef_ImageID_maps    += $(jsonsrc_mariadb_ImageID),$(desired_mariadb_ImageID)

.PHONY: default docker_buildimage docker_svcdef-% migrations clean-migrations

#
# The serviced binary referenced by SVCDEF_EXE is injected into the build
# container by logic in pkg/makefile.
#
# If the JSON syntax (schema) for a service definition is modified, then those modifications
# will not be compiled into new service definitions until a new version of the
# serviced binary is used for this build.  To update the version of the serviced binary
# used for this build, change the SERVICED_ARCHIVE variable in pkg/makefile.
#
SVCDEF_EXE = pkg/serviced
$(SVCDEF_EXE):
	cd $(shell dirname $@) && make $(shell basename $@)

#---------------------#
# Service Definitions #
#---------------------#

#
# Generate service definition template from disparate
# json source:
#
# services/Zenoss.<product>/*.json
#        |
#   +---------------------------+
#   | serviced template compile |
#   +---------------------------+
#        |
#        v
# <dir>/svcdef/templates/<zenoss-product>-<tag>.json
# output/<zenoss-product>-<tag>.json
#
# e.g., For sandbox builds: zenoss-core-5.0.0_140705.json
#       For release builds: zenoss-core-5.0.0b1_521.json
#

#-------------------------------------#
# Add entries here to compile
# service definitions for each product
# to be managed by serviced.
#-------------------------------------#
svcdef_PRODUCTS = zenoss-core zenoss-resmgr zenoss-cse
svcdef_SRC_DIR  = services

zenoss-core-$(BUILD_TAG).json_SRC_DIR   := $(svcdef_SRC_DIR)/Zenoss.core
zenoss-core-$(BUILD_TAG).json_SRC       := $(shell find $(zenoss-core-$(BUILD_TAG).json_SRC_DIR) -type f -name '*.json' -print0)

zenoss-resmgr-$(BUILD_TAG).json_SRC_DIR := $(svcdef_SRC_DIR)/Zenoss.resmgr
zenoss-resmgr-$(BUILD_TAG).json_SRC     := $(shell find $(zenoss-resmgr-$(BUILD_TAG).json_SRC_DIR) -type f -name '*.json' -print0)

zenoss-cse-$(BUILD_TAG).json_SRC_DIR := $(svcdef_SRC_DIR)/Zenoss.cse
zenoss-cse-$(BUILD_TAG).json_SRC     := $(shell find $(zenoss-cse-$(BUILD_TAG).json_SRC_DIR) -type f -name '*.json' -print0)
#-------------------------------------#

# Rule to build service defintions for a list of products.
#
#
# e.g., <dir>/templates/zenoss-core-5.0.0_140705.json
#       <dir>/templates/zenoss-resmgr-5.0.0_140705.json
#
svcdef_BUILD_DIR      = pkg/templates
svcdef_BUILD_TARGETS := $(foreach product,$(svcdef_PRODUCTS),$(svcdef_BUILD_DIR)/$(product)-$(BUILD_TAG).json)

.SECONDEXPANSION:
$(svcdef_BUILD_TARGETS): short_product = $(patsubst zenoss-%,%,$(patsubst %-$(BUILD_TAG).json,%,$(@F)))
$(svcdef_BUILD_TARGETS): map_opt       = $(patsubst %,-map %,$(svcdef_ImageID_maps))
$(svcdef_BUILD_TARGETS): src_dir       = $($(@F)_SRC_DIR)
$(svcdef_BUILD_TARGETS): | $(SVCDEF_EXE) $(OUTPUT) $$(@D)
	@echo "Compiling service definitions with the following version of serviced:"
	@$(SVCDEF_EXE) version
	@compile_CMD="$(SVCDEF_EXE) template compile $(map_opt) $(src_dir) > $@" ;\
	echo $${compile_CMD} ;\
	eval $${compile_CMD} ;\
	rc=$$? ;\
	if [ $${rc} -ne 0 ];then \
		echo "Error: Unable to compile service definition." ;\
		echo "       $${compile_CMD}" ;\
		if [ -f "$@" ];then \
			rm $@ ;\
		fi ;\
		exit $${rc} ;\
	fi
	cp $@ $(OUTPUT)

# Convenience target for building just the service definition template.
#
# Usage:  make svcdef-core  or  make svcdef-zenoss-core
#
svcdef-%: product = $(patsubst %,zenoss-%,$(patsubst zenoss-%,%,$*))
svcdef-%: target  = $(svcdef_BUILD_DIR)/$(product)-$(BUILD_TAG).json
svcdef-%: | $(svcdef_BUILD_DIR)
	$(MAKE) $(target)

######################
# Dockerized targets #
#####################

image/Dockerfile: image/Dockerfile.in
	@sed \
		-e "s/%GID%/$(GID)/g" \
		-e "s/%UID%/$(UID)/g" \
		$< > $@

docker_buildimage: image/Dockerfile
	@$(DOCKER) build -t $(BUILD_IMAGE) $(<D)

docker_svcdef-%: docker_buildimage $(OUTPUT)
	$(DOCKER) run \
			--rm \
			-v $(PWD):/mnt/pwd \
			-v $(OUTPUT):/mnt/pwd/output \
			-e "VERSION=$(VERSION)" \
			-e "SHORT_VERSION=$(SHORT_VERSION)" \
			-e "hbase_VERSION=$(hbase_VERSION)" \
			-e "hdfs_VERSION=$(hdfs_VERSION)" \
			-e "opentsdb_VERSION=$(opentsdb_VERSION)" \
			-e "impact_VERSION=$(impact_VERSION)" \
			-e "otsdb_bigtable_VERSION=$(otsdb_bigtable_VERSION)" \
			-e "zing_connector_VERSION=$(zing_connector_VERSION)" \
			-e "zing_api_proxy_VERSION=$(zing_api_proxy_VERSION)" \
			-e "BUILD_NUMBER=$(_BUILD_NUMBER)" \
			-e "IMAGE_NUMBER=$(IMAGE_NUMBER)" \
			-e "MILESTONE=$(MILESTONE)" \
			-e "RELEASE_PHASE=$(RELEASE_PHASE)" \
			-w /mnt/pwd \
			-u builder \
			$(BUILD_IMAGE) \
			make svcdef-$*

clean: clean-migrations
	@rm -f image/Dockerfile
	@for dir in $(MKDIRS) ;\
	do \
		if [ -d $${dir} ];then \
			echo "rm -rf $${dir}" ;\
			rm -rf $${dir} ;\
		fi ;\
	done
	@make -C pkg clean

MKDIRS = $(OUTPUT) buildroot buildroot/output $(svcdef_BUILD_DIR)

$(MKDIRS):
	@if [ ! -d "$@" ];then \
		echo "mkdir -p $@" ;\
		mkdir -p $@ ;\
	fi

###############################
# zenservicemigration package #
###############################

build-migrations: docker_buildimage $(OUTPUT)
	$(DOCKER) run \
			--rm \
			-v $(PWD):/mnt/pwd \
			-v $(OUTPUT):/mnt/pwd/output \
			-e "VERSION=$(VERSION)" \
			-e "BUILD_NUMBER=$(_BUILD_NUMBER)" \
			-e "IMAGE_NUMBER=$(IMAGE_NUMBER)" \
			-e "MILESTONE=$(MILESTONE)" \
			-e "RELEASE_PHASE=$(RELEASE_PHASE)" \
			-w /mnt/pwd \
			-u builder \
			$(BUILD_IMAGE) \
			make -C migrations wheel
	cp migrations/dist/*.whl output/

clean-migrations:
	@make -C migrations clean
