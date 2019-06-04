timestamps {

node ('x86-fleet') {

	stage ('mobileproduct - Cleanup') {
	 cleanWs()
        }

	stage ('mobileproduct - Checkout') {
	 checkout scm
	 checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: '../mobileproduct']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'GithubAutomation', url: 'https://github.com/Bugatone/mobileproduct']]])
         checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: '../Bugatone-Space']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'GithubAutomation', url: 'https://github.com/Bugatone/Bugatone-Space']]])
	 checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: '../oppo_daemon']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'GithubAutomation', url: 'https://github.com/Bugatone/oppo_daemon']]])
	 checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: '../buga-recordings']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'GithubAutomation', url: 'https://github.com/Bugatone/buga-recordings']]])
	}
	
	timeout(30) {
		stage ('mobileproduct - Build') {
			try {
				sh '''
					#!/bin/bash
					SAVED_CWD=`pwd`
					BUGATONE_ROOT=/var/lib/jenkins/workspace/Bugatone-Space ; export BUGATONE_ROOT
					TEST_FILES_PATH=/var/lib/jenkins/workspace/test-files ; export TEST_FILES_PATH
					LD_LIBRARY_PATH=.:/var/lib/jenkins/workspace/Bugatone-Space/lib/linux_x86:$LD_LIBRARY_PATH ; export LD_LIBRARY_PATH
					PATH=.:/var/lib/jenkins/workspace/Bugatone-Space/bin/linux_x86:$PATH ; export PATH
					PYTHONPATH=/var/lib/jenkins/workspace/Bugatone-Space/python ; export PYTHONPATH
					cd ../Bugatone-Space && ./make.sh linux && pip install -e . --user
					cd $SAVED_CWD/cpp
					./make.py linux
					./make.py android
					cd $SAVED_CWD
					cd ../mobileproduct
					pip install -e ../buga-recordings --user
					pip install -e $SAVED_CWD --user
					pip install -e . --user
					./make.py -c -p

					cd $SAVED_CWD
					if [ -z "${CHANGE_ID}" ]
					then
						context=commits
						page=`git rev-parse HEAD`
						description="commit $page"
					else
						context=issues
						page=${CHANGE_ID}
						description="branch ${CHANGE_BRANCH}"
					fi

					curl -u automation@bugatone.com:bugaAuto1 -s -X POST -d "{\\"body\\": \\"Build number ${BUILD_NUMBER} passed for $description.\\nSee ${BUILD_URL}console\\"}" "https://api.github.com/repos/Bugatone/device_communication/$context/$page/comments"
				'''
			}
			catch(exc) {
				sh '''
					if [ -z "${CHANGE_ID}" ]
					then
						context=commits
						page=`git rev-parse HEAD`
						description="commit $page"
						tags="\\n@noharh @karpadbugatone"
					else
						context=issues
						page=${CHANGE_ID}
						description="branch ${CHANGE_BRANCH}"
					fi

					curl -u automation@bugatone.com:bugaAuto1 -s -X POST -d "{\\"body\\": \\"Build number ${BUILD_NUMBER} failed for $description.\\nSee ${BUILD_URL}console$tags\\"}" "https://api.github.com/repos/Bugatone/device_communication/$context/$page/comments"
				'''
				throw exc
			}
		}
	}
	// stage ('mobileproduct - Postbuild') {
	//   githubPRComment comment: githubPRMessage('Build ${BUILD_NUMBER} ${BUILD_STATUS}')
	//}
}
}
