#!groovy
@Library(["blv-global-jenkins-cicd-shared-library@feature/bugfix-tag"]) _

pipeline {
    agent {
        label 'dockle&&helm'
    }

    options { buildDiscarder(logRotator(numToKeepStr: '30')) }

    environment {
        // Override defaultvalues below

        // Approval
        // approval = true

        // Mattermost
        submitter = '~ai-hub-jenkins--build'

        // Set release branch. Ex. master or regex  ~'release.*' etc.
        // releasebranch = 'master'

        // Set path to deployjob
        deployjobname = 'ai-hub/build/bms'

        // Override default approval for prod-deployment
        // If set to true no approval for deployment in prod is necessary
        // proddeployment = false

        // Set to framework maven/node etc.
        frameworktype = 'python'

        // Set targets. For multiple targets to be choosed set commaseparated
        // releasetarget = 'system'
        // developtarget = ''
        // defaulttarget = ''

        // Set override pom.xml properties.kubernetes.namespace
        // namespace = ''

        // Set override pom.xml properties.kubernetes.cluster.clustertags
        // clustertags = 'backend'

        // Set override on default sonarinstance=sonar
        // sonarinstance = 'sonar'

        // dryrun = false
        // useQualityGate = true
        // abortIfQualityGateFail = true
    }

    stages {
        stage("Prepare") {
            steps {
                script {
                    cicd_buildstate = cicd_prepare()
                }
            }
        }

        stage("Check version") {
            steps {
                script {
                    if (cicd_buildstate.buildType == 'release') {
                        if (! cicd_check_if_release_version(cicd_buildstate.tag) ) {
                            cicd_log.ERROR("${cicd_buildstate.tag} is not a releaseversion. Aborting!")
                        }
                        withCredentials([usernameColonPassword(credentialsId: 'blv-ci-harbor-intern-bolagsverket', variable: 'HELM_CREDS')]) {
                            harborresponse = cicd_callRestGet("api/repositories/${cicd_buildstate.imageName}/tags/${cicd_buildstate.tag}/labels", HELM_CREDS)
                        }
                        if (harborresponse[0] == 200) {
                            cicd_log.ERROR("Releaseversion already uploaded to harbor -> ${cicd_buildstate.imageName}:${cicd_buildstate.tag}. Rebuild new releaseversion!")
                        }
                    }
                }
            }
        }

        stage('Paralell Build, Sonar') {
            failFast true
            parallel {
                stage('Build, test and testcoverage') {
                    steps {
                        script {
                            cicd_log.INFO('tests for python here')
                            image = docker.build(cicd_buildstate.image, '-f helm/dockerfiles/Dockerfile.bms .')
                            image.inside("--entrypoint='' -u 1000") {
                                sh "python -m pipenv run python -m unittest"
                            }
                        }
                    }
                }
                stage('Sonar') {
                    steps {
                        script {
                            // cicd_run_sonar(cicd_buildstate)
                            println("Skipping sonar linter...")
                        }
                    }
                }
            }
        }

        // Om man vill invänta resultat av analys och eventuellt sätta status på bygget
        stage("Sonar Quality Gate") {
            steps {
                script {
                    if (cicd_buildstate.useQualityGate) {
                        timeout(time: 1, unit: 'HOURS') {
                            waitForQualityGate(abortPipeline: cicd_buildstate.abortIfQualityGateFail)
                        }
                    }
                }
            }
        }

        stage('Parallel Trivy and Dockle') {
            failFast true
            parallel {
                stage('Trivy') {
                    steps {
                        script {
                            cicd_log.INFO("Trivy ${cicd_buildstate.image}")
                            cicd_trivyCheck cicd_buildstate.image
                        }
                    }
                }
                stage('Dockle') {
                    steps {
                        script {
                            cicd_log.INFO("Dockle ${cicd_buildstate.image}")
                            cicd_dockleCheck cicd_buildstate.image
                        }
                    }
                }
            }
        }

        stage('Parallel push image and helm') {
            failFast true
            parallel {
                stage('Push image') {
                    steps {
                        script {
                            cicd_push_image(cicd_buildstate, image)
                        }
                    }
                }
                stage('Push helm') {
                    steps {
                        script {
                            cicd_push_helm(cicd_buildstate)
                        }
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    cicd_deploy(cicd_buildstate)
                }
            }
        }
    }
}
