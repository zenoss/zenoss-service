# This file is injected by ControlCenter with container-specific parameters
# ZK_HOST={{with $zks := (child (child (parent .) "HBase") "ZooKeeper").Instances }}{{range (each $zks)}}127.0.0.1:{{plus 2181 .}}{{if ne (plus 1 .) $zks}},{{end}}{{end}}{{end}}/solr
SOLR_JAVA_MEM="-Xms{{.RAMCommitment}} -Xmx{{.RAMCommitment}}"

