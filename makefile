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

# VERSION is the full Zenoss version; e.g., 5.0.0
# SHORT_VERSION is the two-digit Zenoss version; e.g., 5.0
VERSION         ?= 5.1.1
SHORT_VERSION   ?= 5.1

# These three xyz_VERSION variables define the corresponding docker image versions
hbase_VERSION    ?= v16
hdfs_VERSION     ?= v4
opentsdb_VERSION ?= v23

DOCKER          ?= $(shell which docker)
BUILD_NUMBER    ?= $(shell date +%Y%m%d%H%M%S)
#
# Latch in the date with an immediate assignment to avoid
# date roll-over edge case incurred by lazy evaluation.
#
_BUILD_NUMBER    := $(BUILD_NUMBER)
BUILD_IMAGE      ?= "zenoss/svcdefbuild:trusty"
SRCROOT          ?= $(shell pwd)/src
BUILD_TYPE       ?= core
BUILD_NAME       ?= zenoss_$(BUILD_TYPE)-$(VERSION)
PREFIX           ?= /opt/zenoss
OUTPUT           ?= $(PWD)/output
MILESTONE        ?= unstable # unstable | testing | stable
MILESTONE_SUFFIX  =
RELEASE_PHASE    ?= # eg, BETA2 | ALPHA1 | CR13 | 1 | 2 | <blank>
_RELEASE_PHASE   := $(strip $(RELEASE_PHASE))
PWD				  = $(shell pwd)
UID				  = $(shell id -u)

# Allow milestone to influence our artifact versioning.
BUILD_TAG      = $($(strip $(MILESTONE))_TAG)
stable_TAG     = $(VERSION)_$(_RELEASE_PHASE)
testing_TAG    = $(VERSION)_$(_RELEASE_PHASE)
unstable_TAG   = $(VERSION)_$(_BUILD_NUMBER)

# Suck in reference to an image
IMAGE_NUMBER        ?= ""
IMAGE_TAG            = $($(strip $(MILESTONE))_IMAGE_TAG)
stable_IMAGE_TAG     = $(VERSION)_$(_RELEASE_PHASE)
testing_IMAGE_TAG    = $(VERSION)_$(_RELEASE_PHASE)
unstable_IMAGE_TAG   = $(VERSION)_$(IMAGE_NUMBER)_unstable

# Describe docker repositories where we push entitled content.
repo_name_suffix      := _$(SHORT_VERSION)

docker.io_REGPATH     =
docker.io_USER        = zenoss
docker.io_core_REPO   = core$(repo_name_suffix)
docker.io_resmgr_REPO = resmgr$(repo_name_suffix)
docker.io_ucspm_REPO  = ucspm$(repo_name_suffix)
docker.io_cse_REPO    = cse$(repo_name_suffix)
docker.io_SUFFIX      = $(MILESTONE_SUFFIX)

docker_HOST           = docker.io
docker_PREFIX         = $($(docker_HOST)_REGPATH)$($(docker_HOST)_USER)/

#
# docker_HOST         docker_PREFIX
# ------------------  -------------------
# docker.io           zenoss/
#

# Mechanism for overriding ImageIDs in service definition json source:
#
# from: ImageID: "zenoss/zenoss5x"
# into: ImageID: "zenoss/core_5.1:5.1.1_78_unstable"

jsonsrc_zenoss_ImageID = zenoss/zenoss5x
desired_zenoss_ImageID = $(docker_PREFIX)$($(docker_HOST)_$(short_product)_REPO)$($(docker_HOST)_SUFFIX):$(IMAGE_TAG)
svcdef_ImageID_maps   += $(jsonsrc_zenoss_ImageID),$(desired_zenoss_ImageID)

#
# Allow json to be updated automatically at build time if we switch publish
# repos in the makefile.
#
# NB: jsonsrc_<prod>_ImageID = what is currently in the source code.
#     desired_<prod>_ImageID = what you want the ID to be
#
jsonsrc_hbase_ImageID = zenoss/hbase:xx
desired_hbase_ImageID = $(docker_PREFIX)hbase:$(hbase_VERSION)
svcdef_ImageID_maps  += $(jsonsrc_hbase_ImageID),$(desired_hbase_ImageID)
#
jsonsrc_hdfs_ImageID = zenoss/hdfs:xx
desired_hdfs_ImageID = $(docker_PREFIX)hdfs:$(hdfs_VERSION)
svcdef_ImageID_maps  += $(jsonsrc_hdfs_ImageID),$(desired_hdfs_ImageID)
#
jsonsrc_opentsdb_ImageID = zenoss/opentsdb:xx
desired_opentsdb_ImageID = $(docker_PREFIX)opentsdb:$(opentsdb_VERSION)
svcdef_ImageID_maps     += $(jsonsrc_opentsdb_ImageID),$(desired_opentsdb_ImageID)
#
jsonsrc_mariadb_ImageID = zenoss/mariadb:xx
desired_mariadb_ImageID = $(docker_PREFIX)mariadb:10.1-$(IMAGE_TAG)
svcdef_ImageID_maps     += $(jsonsrc_mariadb_ImageID),$(desired_mariadb_ImageID)

.PHONY: default docker_buildimage docker_svcdefpkg-% docker_svcdef-%


$(SRCROOT):
	services

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
svcdef_PRODUCTS = zenoss-core zenoss-resmgr zenoss-ucspm zenoss-cse
svcdef_SRC_DIR  = services

zenoss-core-$(BUILD_TAG).json_SRC_DIR   := $(svcdef_SRC_DIR)/Zenoss.core
zenoss-core-$(BUILD_TAG).json_SRC       := $(shell find $(zenoss-core-$(BUILD_TAG).json_SRC_DIR) -type f -name '*.json' -print0)

zenoss-resmgr-$(BUILD_TAG).json_SRC_DIR := $(svcdef_SRC_DIR)/Zenoss.resmgr
zenoss-resmgr-$(BUILD_TAG).json_SRC     := $(shell find $(zenoss-resmgr-$(BUILD_TAG).json_SRC_DIR) -type f -name '*.json' -print0)

zenoss-ucspm-$(BUILD_TAG).json_SRC_DIR := $(svcdef_SRC_DIR)/ucspm
zenoss-ucspm-$(BUILD_TAG).json_SRC     := $(shell find $(zenoss-ucspm-$(BUILD_TAG).json_SRC_DIR) -type f -name '*.json' -print0)

zenoss-cse-$(BUILD_TAG).json_SRC_DIR := $(svcdef_SRC_DIR)/Zenoss.cse
zenoss-cse-$(BUILD_TAG).json_SRC     := $(shell find $(zenoss-cse-$(BUILD_TAG).json_SRC_DIR) -type f -name '*.json' -print0)
#-------------------------------------#

# Rule to build service defintions for a list of products.
#
#
# e.g., <dir>/templates/zenoss-core-5.0.0_140705.json
#       <dir>/templates/zenoss-resmgr-5.0.0_140705.json
#       <dir>/templates/zenoss-ucspm-5.0.0_140705.json
#
svcdef_BUILD_DIR      = pkg/templates
svcdef_BUILD_TARGETS := $(foreach product,$(svcdef_PRODUCTS),$(svcdef_BUILD_DIR)/$(product)-$(BUILD_TAG).json)
.SECONDEXPANSION:
$(svcdef_BUILD_TARGETS): short_product = $(patsubst zenoss-%,%,$(patsubst %-$(BUILD_TAG).json,%,$(@F)))
$(svcdef_BUILD_TARGETS): map_opt       = $(patsubst %,-map %,$(svcdef_ImageID_maps))
$(svcdef_BUILD_TARGETS): src_dir       = $($(@F)_SRC_DIR)
$(svcdef_BUILD_TARGETS): $$($$(@F)_SRC) | $(SVCDEF_EXE) $(OUTPUT) $$(@D)
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

svcdefpkg-%: product = $(patsubst %,zenoss-%,$(patsubst zenoss-%,%,$*))
svcdefpkg-%: | $(svcdef_BUILD_DIR) $(OUTPUT)
	cd pkg && make clean
	# Generate service definitions for this tag
	$(MAKE) $(svcdef_BUILD_DIR)/$(product)-$(BUILD_TAG).json
	# Package the template
	cd pkg && make \
		VERSION=$(VERSION) \
		BUILD_NUMBER=$(BUILD_NUMBER) \
		RELEASE_PHASE=$(_RELEASE_PHASE) \
		NAME=$(product) \
		TEMPLATE_FILE=../$(svcdef_BUILD_DIR)/$(product)-$(BUILD_TAG).json \
		deb
	cp pkg/$(product)-*.deb $(OUTPUT)
	cd pkg && make \
		VERSION=$(VERSION) \
		BUILD_NUMBER=$(BUILD_NUMBER) \
		RELEASE_PHASE=$(_RELEASE_PHASE) \
		NAME=$(product) \
		TEMPLATE_FILE=../$(svcdef_BUILD_DIR)/$(product)-$(BUILD_TAG).json \
		rpm
	cp pkg/$(product)-*.rpm $(OUTPUT)

######################
# Dockerized targets #
#####################

docker_buildimage:
	$(DOCKER) build -t $(BUILD_IMAGE) hack/

docker_svcdefpkg-%: docker_buildimage $(OUTPUT)
	$(DOCKER) run --rm -v $(PWD):/mnt/pwd \
		-v $(OUTPUT):/mnt/pwd/output \
		-w /mnt/pwd \
		$(BUILD_IMAGE) \
		bash -c '/mnt/pwd/pkg/add_user.sh $(UID) && su serviceduser -c "make \
			VERSION=$(VERSION) \
			SHORT_VERSION=$(SHORT_VERSION) \
			hbase_VERSION=$(hbase_VERSION) \
			hdfs_VERSION=$(hdfs_VERSION) \
			opentsdb_VERSION=$(opentsdb_VERSION) \
			BUILD_NUMBER=$(_BUILD_NUMBER) \
			IMAGE_NUMBER=$(IMAGE_NUMBER) \
			MILESTONE=$(MILESTONE) \
			RELEASE_PHASE=$(RELEASE_PHASE) \
			svcdefpkg-$*"'

clean:
	@for dir in $(MKDIRS) ;\
	do \
		if [ -d $${dir} ];then \
			echo "rm -rf $${dir}" ;\
			rm -rf $${dir} ;\
		fi ;\
	done
	cd pkg && make clean

MKDIRS = $(OUTPUT) buildroot buildroot/output $(svcdef_BUILD_DIR)
$(MKDIRS):
	@if [ ! -d "$@" ];then \
		echo "mkdir -p $@" ;\
		mkdir -p $@ ;\
	fi
