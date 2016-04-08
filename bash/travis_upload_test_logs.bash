#! /bin/bash
#

RESULT_DIR=${1}
BRANCH=${TRAVIS_BRANCH}
if [ "x${TRAVIS_PULL_REQUEST}" != "xfalse" ] ; then
    BRANCH=PR_${TRAVIS_PULL_REQUEST}_to_${BRANCH}
fi
cd
rm -rf logs
# TRAVIS_REPO_SLUG example: dune-community/dune-xt-common
if [ "x${GH_TOKEN}" != "x" ] ; then
  TESTLOGS_URL=https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}-testlogs.git
else
  TESTLOGS_URL=git@github.com:${TRAVIS_REPO_SLUG}-testlogs.git
fi
git clone ${TESTLOGS_URL} logs
cd logs
# check if branch exists, see http://stackoverflow.com/questions/8223906/how-to-check-if-remote-branch-exists-on-a-given-remote-repository
if [ `git ls-remote --heads ${TESTLOGS_URL} ${BRANCH} | wc -l` -ne 0 ] ; then
git checkout ${BRANCH}
else
git checkout -b ${BRANCH}
fi
DIR=${CXX}
if [ "x${MODULES_TO_DELETE}" != "x" ] ; then
    DIR=${DIR}__wo_${MODULES_TO_DELETE// /_}
fi
rm -rf ${DIR}
mkdir ${DIR}
rsync -a ${RESULT_DIR}/*.xml ${DIR}
printenv | grep -v TOKEN | sort > ${DIR}/env
git add --all .
git config user.name "DUNE Community Bot"
git config user.email "dune-community.bot@wwu.de"
git commit -m "Testlogs for Job ${TRAVIS_JOB_NUMBER} - ${TRAVIS_COMMIT_RANGE}"
git push -q --set-upstream origin ${BRANCH}
