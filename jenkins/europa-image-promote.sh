#!/usr/bin/env bash
#
# http://jenkins.zendev.org/view/Promotions/job/europa-image-promote/configure
#

set -e
set -x

repo_tag() {
    flavor="$1"        # examples: core, resmgr
    maturity="$2"      # examples: stable, testing, unstable
    phase="$3"         # examples for testing: BETA1, CR13, GA
                       # examples for stable: 1, 2, 3
    # repo name: e.g., zenoss/resmgr_5.0
    repo="zenoss/${flavor}_${SHORT_VERSION}"
    case $maturity in
        unstable )
            # e.g., 5.0.0_1234_unstable
            tag="${VERSION}_${IMAGE_FROM_BUILDNUMBER}_unstable"
            ;;
        testing )
            # e.g., 5.0.0_CR13
            tag="${VERSION}_${phase}"
            ;;
        stable )
            # e.g., 5.0.0_2
            tag="${VERSION}_${phase}"
            ;;
        * )
            exit 1
            ;;
    esac

    echo ${repo}:${tag}
}

retry() {
    local maxtries=$1; shift
    local sleeptime=$1; shift
    local command="$@"
    local tries=0
    until [ ${tries} -ge ${maxtries} ]; do
        set +e
        ${command};
        local result=$?;
        set -e
        [ ${result} = 0 ] && break
        tries=$[$tries+1]
        echo sleeping $sleeptime before retry
        sleep $sleeptime
    done
    return ${result}
}

case $VERSION in
    *)
        # No quoting FLAVORS below in order to split the string on spaces
        for FLAVOR in $FLAVORS; do
            FROM_STRING=$(repo_tag "$FLAVOR" "$FROM_MATURITY" "$FROM_RELEASEPHASE")
            TO_STRING=$(repo_tag "$FLAVOR" "$TO_MATURITY" "$TO_RELEASEPHASE")
            retry 4 5s docker pull "$FROM_STRING"
            docker tag -f "$FROM_STRING" "$TO_STRING"
            retry 10 30s docker push "$TO_STRING"
            if [[ "$TO_MATURITY" = "stable" ]]; then
                retry 4 5s docker pull "$TO_STRING"    # ensure new tag is available
                retry 4 5s docker pull "$FROM_STRING"  # allow a little time for dockerhub
                LATEST_STRING="$(echo $TO_STRING | cut -f1 -d:):${VERSION}"
                docker tag -f "$FROM_STRING" "$LATEST_STRING"
                retry 10 30s docker push "$LATEST_STRING"
            fi
        done
        ;;
esac


