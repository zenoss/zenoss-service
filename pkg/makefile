
THIS_MAKEFILE := $(notdir $(CURDIR)/$(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST)))

#
# RPM and DEB builder for service definitions.
#

# NAME is typically overridden from the toplevel make:
#    e.g. make -f makefile NAME=zenoss-core
#
NAME           = product
FULL_NAME      = $(NAME)-service
VERSION       ?= 5.0.70
RELEASE_PHASE  = # eg, ALPHA1 | BETA1 | CR1 | GA
MAINTAINER     ="Zenoss CM <cm@zenoss.com>"
PKGROOT        = pkgroot/$(FULL_NAME)

# Package versions will follow the following idiom:
#
#   BUILD_NUMBER=1234
#   RELEASE_PHASE=#ignored
#   NIGHTLY: serviced-1.0.0-0.0.1234.unstable (where 1234 is the build number)
#
#   RELEASE_PHASE=ALPHA1
#   BUILD_NUMBER=#ignored
#   TESTING: serviced-1.0.0-0.1.ALPHA1 (where ALPHA1 is the release phase.  Could be any of
#                                       ALPHA#, BETA#, CR#, or GA)
#
#   RELEASE_PHASE=1    # GA
#   BUILD_NUMBER=#ignored
#   STABLE:  serviced-1.0.0-1 (this is special, and will result in a '1' REVISION)
#
#   RELEASE_PHASE=2    # GA2
#   BUILD_NUMBER=#ignored
#   STABLE:  serviced-1.0.0-2 (this is special, and will result in a '2' REVISION)


PKG_VERSION = $(VERSION)
ifeq "$(RELEASE_PHASE)" ""
    ITERATION = 0.0.$(BUILD_NUMBER).unstable
    BUILD_LABEL = build-$(BUILD_NUMBER)
else
    # Included a RELEASE_PHASE - assume NOT a nightly build
    ifeq "$(RELEASE_PHASE)" "$(shell echo $(RELEASE_PHASE) | tr -cd '[:digit:]')"
        ITERATION = $(RELEASE_PHASE)
    else
        ITERATION = 0.1.$(RELEASE_PHASE)
    endif
    BUILD_LABEL =
endif

ifeq "$(FROMVERSION)" ""
DEB_PKG_VERSION=$(PKG_VERSION)
else
DEB_PKG_VERSION = $(FROMVERSION)+$(PKG_VERSION)
endif

define DESCRIPTION
Service definitions for $(NAME).  $(BUILD_LABEL)
These definitions allow $(NAME) to be instantiated by the
Zenoss Control Center serviced application into a runtime environment that
leverages the scalability, performance, and deployment lifecycle associated
with Docker containers.
endef
export DESCRIPTION

.PHONY: all clean deb rpm
.SILENT: desc

all: desc

desc:
	echo "Usage: make deb or make rpm. Both options package $(FULL_NAME)-$(PKG_VERSION)."

.PHONY: clean_files
clean_files:
	@for pkg in *.deb *.rpm serviced;\
	do \
		if [ -f "$${pkg}" ];then \
			echo "rm -f $${pkg}" ;\
			if ! rm -f $${pkg} ;then \
				echo "sudo rm -f $${pkg}" ;\
				if ! sudo rm -f $${pkg} ; then \
					echo "Warning: Unable to remove $${pkg}" ;\
					exit 1 ;\
				fi ;\
			fi ;\
		fi ;\
	done

.PHONY: clean_dirs
clean_dirs = $(PKGROOT) pkgroot templates
clean_dirs:
	@for dir in $(clean_dirs) ;\
	do \
		if [ -d "$${dir}" ];then \
			echo "rm -rf $${dir}" ;\
			if ! rm -rf $${dir} ;then \
				echo "sudo rm -rf $${dir}" ;\
				if ! sudo rm -rf $${dir} ; then \
					echo "Warning: Unable to remove $${dir}" ;\
					exit 1 ;\
				fi ;\
			fi ;\
		fi ;\
	done

# Clean staged files and produced packages
.PHONY: clean
clean: clean_files clean_dirs

.PHONY: mrclean
mrclean: clean

# Install a prebuilt serviced binary from zenpip. If the schema/syntax for
# service definitions changes, you must first rebuild a copy of serviced that
# supports those changes, and then modify this makefile to reference that
# specific binary.
#
# FYI - Prior to CC 1.1.4, the serviced artifacts were identified
#       by git SHA, but starting with CC 1.1.4 and RM 5.1.3, the naming convention
#       for the tgz artifacts was updated to use CC version and build number.
ZENPIPPKGSURL = http://zenpip.zenoss.eng/packages
SERVICED_ARCHIVE=serviced-1.7.0-0.0.368.unstable.tgz
serviced:
	echo " extracting: $@"
	curl -s $(ZENPIPPKGSURL)/$(SERVICED_ARCHIVE) | \
		tar -v -xz --transform 's|.*/||g' ./opt/serviced/bin/serviced

# Make root dir for packaging
$(PKGROOT):
	mkdir -p $@

TEMPLATE_INST = opt/serviced/templates
stage_pkg: $(PKGROOT)
	mkdir -p $(PKGROOT)/$(TEMPLATE_INST)
	cp -p $(TEMPLATE_FILE) $(PKGROOT)/$(TEMPLATE_INST)


# Make a DEB
deb: stage_pkg
	fpm \
		-n $(FULL_NAME) \
		-v $(DEB_PKG_VERSION) \
		--iteration $(ITERATION) \
		-s dir \
		-d serviced \
		-t deb \
		-a noarch \
		-C $(PKGROOT) \
		-m $(MAINTAINER) \
		--description "$$DESCRIPTION" \
		--deb-user root \
		--deb-group root \
		.

# Make an RPM
rpm: stage_pkg
	fpm \
		-n $(FULL_NAME) \
		-v $(PKG_VERSION) \
		--iteration $(ITERATION) \
		-s dir \
		-d serviced \
		-t rpm \
		-a noarch \
		-C $(PKGROOT) \
		-m $(MAINTAINER) \
		--description "$$DESCRIPTION" \
		--rpm-user root \
		--rpm-group root \
		.
