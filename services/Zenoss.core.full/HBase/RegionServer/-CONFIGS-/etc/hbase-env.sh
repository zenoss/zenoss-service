export HBASE_MANAGES_ZK=false
export HBASE_HEAPSIZE={{percentScale (bytesToMB .RAMCommitment) 0.9}}
