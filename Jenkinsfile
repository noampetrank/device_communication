timestamps {

node ('x86') { 

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
	
	stage ('mobileproduct - Build') {
		try {
			sh '''
				#!/bin/bash
				SAVED_CWD=`pwd`
				GIT_AUTOMATION_USER=automation%40bugatone.com
				GIT_AUTOMATION_PASS=bugaAuto1
				BUGATONE_ROOT=/var/lib/jenkins/workspace/Bugatone-Space ; export BUGATONE_ROOT
				TEST_FILES_PATH=/var/lib/jenkins/workspace/test-files ; export TEST_FILES_PATH
				LD_LIBRARY_PATH=.:/var/lib/jenkins/workspace/Bugatone-Space/lib/linux_x86:$LD_LIBRARY_PATH ; export LD_LIBRARY_PATH
				PATH=.:/var/lib/jenkins/workspace/Bugatone-Space/bin/linux_x86:$PATH ; export PATH
				PYTHONPATH=/var/lib/jenkins/workspace/Bugatone-Space/python ; export PYTHONPATH
				git config credential.helper "store --file /home/ubuntu/.git_credentials"
				echo "https://$GIT_AUTOMATION_USER:$GIT_AUTOMATION_PASS@github.com" > /home/ubuntu/.git_credentials
				cd ../Bugatone-Space && ./make.sh linux && pip install -e . --user
				cd ../test-files && git pull
				cd ../mobileproduct
				pip install -e ../buga-recordings --user
				pip install -e $SAVED_CWD --user
				pip install -e . --user
				./make.py -c -p 

				if [ -z "${CHANGE_ID}" ]
				then
					cd $SAVED_CWD
					context=commits
					page=`git rev-parse HEAD`
				else
					context=issues
					page=${CHANGE_ID}
				fi

				curl -u automation@bugatone.com:bugaAuto1 -s -X POST -d "{\\"body\\": \\"Build $BUILD_NUMBER passed.\\nSee ${BUILD_URL}console\\"}" "https://api.github.com/repos/Bugatone/device_communication/$context/$page/comments"
			'''
		} 
		catch(exc) {
			sh '''
				if [ -z "${CHANGE_ID}" ]
				then
					context=commits
					page=`git rev-parse HEAD`
				else
					context=issues
					page=${CHANGE_ID}
				fi

				curl -u automation@bugatone.com:bugaAuto1 -s -X POST -d "{\\"body\\": \\"Build $BUILD_NUMBER failed.\\nSee ${BUILD_URL}console\\"}" "https://api.github.com/repos/Bugatone/device_communication/$context/$page/comments"
			'''
			throw exc
		}
	}
	// stage ('mobileproduct - Postbuild') {
	//   githubPRComment comment: githubPRMessage('Build ${BUILD_NUMBER} ${BUILD_STATUS}')
	//}
}
}
