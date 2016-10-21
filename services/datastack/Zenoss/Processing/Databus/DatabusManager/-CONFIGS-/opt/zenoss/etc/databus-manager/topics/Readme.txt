Topics and their corresponding schemas are grouped into appropriate
sub-directories. Each such grouping represents the databus touchpoints
i.e. the ingress, intermediate staging and egress topics for a
specific operational flow in the Zenoss solution. The schema for each
topic is the advertised content API for both flow-internal and
flow-external (viz. from other related flows or even subsequent
add-ons via zenpacks etc.) processing components to leverage when
publishing to or consuming from these topics.

See "example" for an example.
