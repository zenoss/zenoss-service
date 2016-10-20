#!/usr/bin/env bash

#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# This file is sourced when running various Spark programs.
# Copy it as spark-env.sh and edit that to configure Spark for your site.

# Options read when launching programs locally with
# ./bin/run-example or ./bin/spark-submit
#HADOOP_CONF_DIR=
# to set the IP address Spark binds to on this node
#SPARK_LOCAL_IP=
# - to set the public dns name of the driver program
#SPARK_PUBLIC_DNS=
# - default classpath entries to append
#SPARK_CLASSPATH=

# Options read by executors and drivers running inside the cluster
# -  to set the IP address Spark binds to on this node
#SPARK_LOCAL_IP=
# -  to set the public DNS name of the driver program
#SPARK_PUBLIC_DNS=
# -  default classpath entries to append
#SPARK_CLASSPATH=
# -  storage directories to use on this node for shuffle and RDD data
#SPARK_LOCAL_DIRS=
# -, to point to your libmesos.so if you use Mesos
#MESOS_NATIVE_JAVA_LIBRARY=


# Options for the daemons used in the standalone deploy mode
# - SPARK_MASTER_IP, to bind the master to a different IP address or hostname

# - SPARK_WORKER_CORES, to set the number of cores to use on this machine
# - SPARK_WORKER_MEMORY, to set how much total memory workers have to give executors (e.g. 1000m, 2g)
# - SPARK_WORKER_PORT / SPARK_WORKER_WEBUI_PORT, to use non-default ports for the worker
# - SPARK_WORKER_INSTANCES, to set the number of worker processes per node
# - SPARK_WORKER_DIR, to set the working directory of worker processes
# - SPARK_WORKER_OPTS, to set config properties only for the worker (e.g. "-Dx=y")
# - SPARK_DAEMON_MEMORY, to allocate to the master, worker and history server themselves (default: 1g).
# - SPARK_HISTORY_OPTS, to set config properties only for the history server (e.g. "-Dx=y")
# - SPARK_SHUFFLE_OPTS, to set config properties only for the external shuffle service (e.g. "-Dx=y")
# - SPARK_DAEMON_JAVA_OPTS, to set config properties for all daemons (e.g. "-Dx=y")
# - SPARK_PUBLIC_DNS, to set the public dns name of the master or workers

# Generic options for the daemons used in the standalone deploy mode
# - SPARK_CONF_DIR      Alternate conf dir. (Default: ${SPARK_HOME}/conf)
# - SPARK_LOG_DIR       Where log files are stored.  (Default: ${SPARK_HOME}/logs)
# - SPARK_PID_DIR       Where the pid file is stored. (Default: /tmp)
# - SPARK_IDENT_STRING  A string representing this instance of spark. (Default: $USER)
# - SPARK_NICENESS      The scheduling priority for daemons. (Default: 0)
SPARK_HOME=/opt/spark
SPARK_LOG_DIR=/var/log/spark
SPARK_IDENT_STRING="zenoss"
#SPARK_PUBLIC_DNS, to set the public dns name of the master or workers
#SPARK_MASTER_IP=
SPARK_MASTER_PORT=7077
SPARK_MASTER_WEBUI_PORT=8080
# 
SPARK_COMMON_OPTS="-Dspark.driver.port=7001 -Dspark.fileserver.port=7002 
 -Dspark.broadcast.port=7003 -Dspark.replClassServer.port=7004 
 -Dspark.blockManager.port=7005 -Dspark.executor.port=7006 
 -Dspark.ui.port=4040 -Dspark.broadcast.factory=org.apache.spark.broadcast.HttpBroadcastFactory"
SPARK_MASTER_OPTS="$SPARK_COMMON_OPTS -Dspark.deploy.defaultCores=3"
SPARK_WORKER_OPTS="$SPARK_COMMON_OPTS -Dspark.worker.cleanup.enabled=true"
#SPARK_LOCAL_DIRS=
# - SPARK_WORKER_CORES, to set the number of cores to use on this machine
# - SPARK_WORKER_MEMORY, to set how much total memory workers have to give executors (e.g. 1000m, 2g)
SPARK_WORKER_PORT=7078
SPARK_WORKER_WEBUI_PORT=8081
# - SPARK_WORKER_INSTANCES, to set the number of worker processes per node
# - SPARK_WORKER_DIR, to set the working directory of worker processes
# - SPARK_WORKER_OPTS, to set config properties only for the worker (e.g. "-Dx=y")
#SPARK_DAEMON_JAVA_OPTS="-Dspark.deploy.recoveryMode=ZOOKEEPER -Dspark.deploy.zookeeper.dir=/datapipeline/spark -Dspark.deploy.zookeeper.url=COMMA_SEPARATED_LIST_OF_HOST_PORT"
