
THIS_MAKEFILE := $(notdir $(CURDIR)/$(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST)))

#
# RPM and DEB builder for service definitions.
#

# NAME is typically overridden from the toplevel make:
#    e.g. make -f makefile NAME=zenoss-core
#
NAME          = product
FULL_NAME     = $(NAME)-service
#FROMVERSION  = 0.3.70
VERSION       = 5.0.0
RELEASE_PHASE = # eg, b2 | a1 | rc1 | <blank>
MAINTAINER    ="Zenoss CM <cm@zenoss.com>"
PKGROOT       = pkgroot/$(FULL_NAME)

# A build number is only expected on nightly 'unstable' builds, and will be
# included as part of the package's version.  If a release phase is 
# included, the build number will be left off the package version.
ifeq "$(RELEASE_PHASE)" ""
PKG_VERSION = $(VERSION)-$(BUILD_NUMBER)
else
PKG_VERSION = $(VERSION)$(RELEASE_PHASE)
endif

ifeq "$(FROMVERSION)" ""
DEB_PKG_VERSION=$(PKG_VERSION)
else
DEB_PKG_VERSION = $(FROMVERSION)+$(PKG_VERSION)
endif

define DESCRIPTION
Service definitions for $(NAME).
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
	for pkg in *.deb *.rpm serviced;\
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
	for dir in $(clean_dirs) ;\
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

# Install built serviced binary from zenpip tgz
ZENPIPPKGSURL = http://zenpip.zendev.org/packages
serviced:
	echo " extracting: $@"
	curl -s $(ZENPIPPKGSURL)/serviced-e80a617cd935bb27df28d8056fea578bc7a08adb.tgz | \
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
