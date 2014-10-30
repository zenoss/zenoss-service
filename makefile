VERSION         ?= 5.0.0
hbase_VERSION    = v3
opentsdb_VERSION = v8

DOCKER          ?= $(shell which docker)
BUILD_NUMBER    ?= $(shell date +%y%m%d)
#
# Latch in the date with an immediate assignment to avoid
# date roll-over edge case incurred by lazy evaluation.
#
_BUILD_NUMBER    := $(BUILD_NUMBER)
BUILD_IMAGE      ?= "zenoss/rpmbuild:centos7"
SRCROOT          ?= $(shell pwd)/src
BUILD_TYPE       ?= core
BUILD_NAME       ?= zenoss_$(BUILD_TYPE)-$(VERSION)
PREFIX           ?= /opt/zenoss
OUTPUT           ?= $(PWD)/output
MILESTONE        ?= unstable # unstable | testing | stable
MILESTONE_SUFFIX  = $(patsubst %,-%,$(strip $(MILESTONE)))
RELEASE_PHASE    ?= # eg, b2 | a1 | rc1 | <blank>
_RELEASE_PHASE   := $(strip $(RELEASE_PHASE))

# Allow milestone to influence our artifact versioning.
IMAGE_TAG      = $($(strip $(MILESTONE))_TAG)
stable_TAG     = $(VERSION)
testing_TAG    = $(VERSION)$(_RELEASE_PHASE)_$(_BUILD_NUMBER)
unstable_TAG   = $(VERSION)_$(_BUILD_NUMBER)

# Describe docker repositories where we push entitled content.
quay.io_REGPATH       = quay.io/
quay.io_USER          = zenossinc
quay.io_core_REPO     = zenoss-core
quay.io_resmgr_REPO   = zenoss-resmgr
quay.io_SUFFIX        = $(MILESTONE_SUFFIX)

docker.io_REGPATH     =
docker.io_USER        = zenoss
docker.io_core_REPO   = core
docker.io_resmgr_REPO = resmgr
docker.io_SUFFIX      = $(MILESTONE_SUFFIX)

docker_HOST           = docker.io
docker_PREFIX         = $($(docker_HOST)_REGPATH)$($(docker_HOST)_USER)/
#
# docker_HOST         docker_PREFIX
# ------------------  -------------------
# docker.io           zenoss/
# quay.io             quay.io/zenossinc/
#

# Mechanism for overriding ImageIDs in service definition json source:
#
# from: ImageID: "zenoss/zenoss5x" 
# into: ImageID: "quay.io/zenossinc/zenoss-core-testing:5.0.0b1_521"

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
jsonsrc_hbase_ImageID = zenoss/hbase:v3
desired_hbase_ImageID = $(docker_PREFIX)hbase:$(hbase_VERSION)
svcdef_ImageID_maps  += $(jsonsrc_hbase_ImageID),$(desired_hbase_ImageID)
#
jsonsrc_opentsdb_ImageID = zenoss/opentsdb:v8
desired_opentsdb_ImageID = $(docker_PREFIX)opentsdb:$(opentsdb_VERSION)
svcdef_ImageID_maps     += $(jsonsrc_opentsdb_ImageID),$(desired_opentsdb_ImageID)

.PHONY: default

$(SRCROOT):
	services

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
svcdef_PRODUCTS = zenoss-core zenoss-resmgr
svcdef_SRC_DIR  = services

zenoss-core-$(IMAGE_TAG).json_SRC_DIR   := $(svcdef_SRC_DIR)/Zenoss.core
zenoss-core-$(IMAGE_TAG).json_SRC       := $(shell find $(zenoss-core-$(IMAGE_TAG).json_SRC_DIR) -type f -name '*.json')

zenoss-resmgr-$(IMAGE_TAG).json_SRC_DIR := $(svcdef_SRC_DIR)/Zenoss.resmgr
zenoss-resmgr-$(IMAGE_TAG).json_SRC     := $(shell find $(zenoss-resmgr-$(IMAGE_TAG).json_SRC_DIR) -type f -name '*.json')
#-------------------------------------#
 
# Rule to build service defintions for a list of products.
#
#
# e.g., <dir>/templates/zenoss-core-5.0.0_140705.json
#       <dir>/templates/zenoss-resmgr-5.0.0_140705.json
#
svcdef_BUILD_DIR      = pkg/templates
svcdef_BUILD_TARGETS := $(foreach product,$(svcdef_PRODUCTS),$(svcdef_BUILD_DIR)/$(product)-$(IMAGE_TAG).json)
.SECONDEXPANSION:
$(svcdef_BUILD_TARGETS): short_product = $(patsubst zenoss-%,%,$(patsubst %-$(IMAGE_TAG).json,%,$(@F)))
$(svcdef_BUILD_TARGETS): map_opt       = $(patsubst %,-map %,$(svcdef_ImageID_maps))
$(svcdef_BUILD_TARGETS): src_dir       = $($(@F)_SRC_DIR)
$(svcdef_BUILD_TARGETS): $$($$(@F)_SRC) | $(SVCDEF_EXE) $(OUTPUT) $$(@D)
	@compile_CMD="$(SVCDEF_EXE) template compile $(map_opt) $(src_dir) > $@" ;\
	echo $${compile_CMD} ;\
	eval $${compile_CMD} 2>/dev/null ;\
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
svcdef-%: target  = $(svcdef_BUILD_DIR)/$(product)-$(IMAGE_TAG).json
svcdef-%: | $(svcdef_BUILD_DIR)
	$(MAKE) $(target)

svcdefpkg-%: product = $(patsubst %,zenoss-%,$(patsubst zenoss-%,%,$*))
svcdefpkg-%: | $(svcdef_BUILD_DIR) $(OUTPUT)
	cd pkg && make clean
	# Generate service definitions for this tag
	$(MAKE) $(svcdef_BUILD_DIR)/$(product)-$(IMAGE_TAG).json
	# Package the template
	cd pkg && make \
		VERSION=$(VERSION) \
		BUILD_NUMBER=$(_BUILD_NUMBER) \
		RELEASE_PHASE=$(_RELEASE_PHASE) \
		NAME=$(product) \
		TEMPLATE_FILE=../$(svcdef_BUILD_DIR)/$(product)-$(IMAGE_TAG).json \
		deb
	cp pkg/$(product)-*.deb $(OUTPUT)
	cd pkg && make \
		VERSION=$(VERSION) \
		BUILD_NUMBER=$(_BUILD_NUMBER) \
		RELEASE_PHASE=$(_RELEASE_PHASE) \
		NAME=$(product) \
		TEMPLATE_FILE=../$(svcdef_BUILD_DIR)/$(product)-$(IMAGE_TAG).json \
		rpm
	cp pkg/$(product)-*.rpm $(OUTPUT)

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
