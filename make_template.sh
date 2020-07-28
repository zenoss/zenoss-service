#!/bin/bash

if [ "$1" == "-h" ] ; then
   echo Usage: $(basename $0) [directory]
   echo
   echo Create a service template from the given directory.  The result is
   echo written to stdout. If no directory is given, the image name
   echo substitutions are printed.
   echo
   echo If the following variables are not found in the environment, their
   echo values are extracted from the version.mk file in product-assembly in
   echo a zendev environment.  If that fails, this script exits with an error.
   echo
   echo "   HBASE_VERSION"
   echo "   HDFS_VERSION"
   echo "   OPENTSDB_VERSION"
   echo "   ZING_CONNECTOR_VERSION"
   echo "   ZING_API_PROXY_VERSION"
   echo "   OTSDB_BIGTABLE_VERSION"
   echo "   IMPACT_VERSION"
   echo
   echo If the ZENOSS_IMAGE_TAG and MARIADB_IMAGE_TAG variables are not set,
   echo their values are set to the name of the current zendev environment.
   echo
   echo If ZENOSS_IMAGE is not set, its value is set to \"zendev/devimg\"
   echo If MARIADB_IMAGE is not set, its value is set to \"zendev/mariadb\"
   echo
   echo If the VERSION variable is not set, the value is read from the VERSION file.
   echo
   echo This script depends on the \'serviced\' command being available.
   echo
   exit 0
fi

zendev=$(which zendev)
if [ $? -eq 0 ] ; then
   zendev_root=$(${zendev} root)
   zendev_env=$(${zendev} env)
   version_file=${zendev_root}/src/github.com/zenoss/product-assembly/versions.mk
   if [ ! -f ${version_file} ]; then
      unset version_file
   fi
   service_version_file=${zendev_root}/src/github.com/zenoss/zenoss-service/VERSION
   if [ ! -f ${service_version_file} ]; then
      unset service_version_file
   fi
fi

function get_variable() {
   local value=${!1}
   if [ -z ${value:+x} ] ; then
      if [ -z ${version_file+x} ]; then
         echo "$1 is not set and product-assembly/versions.mk not found" 1>&2
         exit 1
      fi
      echo $(grep "^\<$1\>" ${version_file} | cut -f2 -d'=')
   fi
   echo ${value}
}

if [ -z ${VERSION:+x} ]; then
   if [ -z ${service_version_file:+x} ]; then
      version=$(get_variable VERSION)
   else
      version=$(cat ${service_version_file})
   fi
else
   version=${VERSION}
fi

if [ -z ${ZENOSS_IMAGE:+x} ]; then
   # ZENOSS_IMAGE is null or not set, assume devimg build
   zenoss_image=zendev/devimg
else
   zenoss_image=${ZENOSS_IMAGE}
fi

if [ -z ${ZENOSS_IMAGE_TAG:+x} ]; then
   # ZENOSS_IMAGE_TAG is null or not set, assume devimg build
   zenoss_tag=${zendev_env}
else
   zenoss_tag=${ZENOSS_IMAGE_TAG}
fi

if [ -z ${MARIADB_IMAGE:+x} ]; then
   # MARIADB_IMAGE is null or not set, assume devimg build
   mariadb_image=zendev/mariadb
else
   mariadb_image=${MARIADB_IMAGE}
fi

if [ -z ${MARIADB_IMAGE_TAG:+x} ]; then
   # MARIADB_IMAGE_TAG is null or not set, assume devimg build
   mariadb_version=${zendev_env}
else
   mariadb_version=${MARIADB_IMAGE_TAG}
fi

hbase_version=$(get_variable HBASE_VERSION) || exit 1
hdfs_version=$(get_variable HDFS_VERSION) || exit 1
opentsdb_version=$(get_variable OPENTSDB_VERSION) || exit 1
zing_connector_version=$(get_variable ZING_CONNECTOR_VERSION) || exit 1
zing_api_proxy_version=$(get_variable ZING_API_PROXY_VERSION) || exit 1
otsdb_bigtable_version=$(get_variable OTSDB_BIGTABLE_VERSION) || exit 1
impact_version=$(get_variable IMPACT_VERSION) || exit 1

# Retrieve the project image name
project_image=$(get_variable IMAGE_PROJECT)
if [ -z ${project_image:+x} ]; then
   # PROJECT_IMAGE is null or not set, set a default
   project_image=zing-registry-188222
fi

bigtable_image=gcr.io/${project_image}/otsdb-bigtable
zing_connector_image=gcr.io/${project_image}/zing-connector
api_key_proxy_image=gcr.io/${project_image}/api-key-proxy

impact_folder=impact_$(echo ${impact_version} | sed -E 's/([0-9]+).([0-9]+).*/\1.\2/')
impact_image=gcr.io/${project_image}/${impact_folder}

if [ "$1" == "" ] ; then
   printf "%-30s %s\n" zenoss/zenoss5x ${zenoss_image}:${zenoss_tag}
   printf "%-30s %s\n" zenoss/mariadb:xx ${mariadb_image}:${mariadb_version}
   printf "%-30s %s\n" zenoss/hbase:xx zenoss/hbase:${hbase_version}
   printf "%-30s %s\n" zenoss/hdfs:xx zenoss/hbase:${hdfs_version}
   printf "%-30s %s\n" zenoss/opentsdb:xx zenoss/opentsdb:${opentsdb_version}
   printf "%-30s %s\n" zenoss/opentsdb-bigtable:xx ${bigtable_image}:${otsdb_bigtable_version}
   printf "%-30s %s\n" gcr-repo/zing-connector:xx ${zing_connector_image}:${zing_connector_version}
   printf "%-30s %s\n" gcr-repo/api-key-proxy:xx ${api_key_proxy_image}:${zing_api_proxy_version}
   printf "%-30s %s\n" zendev/impact-devimg ${impact_image}:${impact_version}
else

   serviced=$(which serviced-service)
   if [ $? -ne 0 ] ; then
      echo "serviced: command not found" 1>&2
      exit 1
   fi

   sed -i -e "s/\"Version\": \".*\",/\"Version\": \"${version}\",/" $1/service.json
   ${serviced} compile \
      --map zenoss/zenoss5x,zendev/devimg:${zenoss_tag} \
      --map zenoss/mariadb:xx,zendev/mariadb:${mariadb_version} \
      --map zenoss/hbase:xx,zenoss/hbase:${hbase_version} \
      --map zenoss/hdfs:xx,zenoss/hbase:${hdfs_version} \
      --map zenoss/opentsdb:xx,zenoss/opentsdb:${opentsdb_version} \
      --map zenoss/opentsdb-bigtable:xx,${bigtable_image}:${otsdb_bigtable_version} \
      --map gcr-repo/zing-connector:xx,${zing_connector_image}:${zing_connector_version} \
      --map gcr-repo/api-key-proxy:xx,${api_key_proxy_image}:${zing_api_proxy_version} \
      --map zendev/impact-devimg,${impact_image}:${impact_version} \
      $1
fi
