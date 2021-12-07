// vars/cicd_prepare.groovy
import se.bolagsverket.pipeline.steps.maven.RunMvnStep
def call() {
    deleteDir()
    repo = checkout(scm)
    gitBranch = repo.GIT_BRANCH
    gitSha = sh(returnStdout: true, script: "git log -n 1 --pretty=format:'%h'").trim()
    gitAuthor = sh(returnStdout: true, script: "git show -s --pretty=%an").trim()
    gitEmail = sh(returnStdout: true, script: "git show -s --pretty=%ae").trim()
    cicd_log.INFO("Checkout ${gitBranch}")
    dryRun = env.dryrun ?: false
    releasebranch = env.releasebranch ?: 'master'
    frameworktype = env.frameworktype ?: 'maven'

    switch (gitBranch) {
        case releasebranch:
            tagprefix = ""
            deploytotarget = env.releasetarget ?: 'system'
            buildtype = 'release'
            break
        case 'develop':
            tagprefix = "-beta-${gitSha}"
            deploytotarget = env.developtarget ?: ''
            buildtype = 'develop'
            break
        default:
            tagprefix = "-alpha-${gitSha}"
            deploytotarget = env.defaulttarget ?: ''
            buildtype = 'feature'
            break
    }

    switch (frameworktype) {
        case 'maven':
            cicd_buildstate {
                build = cicd_mavenPrepareBuild(params + [releaseBranch: /master/])
                tag = build.revision + tagprefix
                build.changelist = ''
                image = build.properties['docker.image.name'] + ':' + tag
                imageName = build.properties['docker.image.name']
                mavenOpts = build.subMap(RunMvnStep.PARAMETERS)
                mavenOpts << [options: ['-Ddocker.tag=' + tag]]
                nameSpace = env.nameSpace?: build.properties['kubernetes.namespace']
                clusterTags = env.clusterTags?: build.properties['kubernetes.clustertags']
            }
            break
        case 'node':
            applicationdata = readJSON file: 'package.json'
            def cicd_buildstate = {
                tag = applicationdata.version + tagprefix
                image = "${applicationdata.imagename}:${tag}"
                imageName = applicationdata.imagename
                nameSpace = applicationdata.namespace ?: 'missing'
                clusterTags = applicationdata.clustertags ?: 'backend'
            }
            break
        default:
            applicationdata = readYaml file: 'release.yaml'
            def cicd_buildstate = {
                tag = applicationdata.version + tagprefix
                image = "${applicationdata.imagename}:${tag}"
                imageName = applicationdata.imagename
                nameSpace = applicationdata.namespace ?: 'missing'
                clusterTags = applicationdata.clustertags ?: 'backend'
            }
            break
    }
    println("Yippi!")
    println(cicd_buildstate)
    cicd_buildstate['approval'] = env.approval ?: 'true'
    cicd_buildstate['dryRun'] = env.dryrun ?: false
    cicd_buildstate['proddeployment'] = env.proddeployment ?: false
    cicd_buildstate['chart'] = readYaml(file: 'helm/Chart.yaml')
    cicd_buildstate.chart << [version: cicd_buildstate.tag, appVersion: cicd_buildstate.tag]
    cicd_buildstate['deployTargets'] = deploytotarget.replaceAll("\\s","").tokenize(",")
    cicd_buildstate['deployTarget'] = ''
    cicd_buildstate['deployJobName'] = env.deployjobname ?: ''
    cicd_buildstate['frameWorkType'] = frameworktype
    cicd_buildstate['buildType'] = buildtype
    cicd_buildstate['currentBuild'] = {'displayName'}
    cicd_buildstate['currentBuild']['displayName'] = "#${env.BUILD_ID} ${cicd_buildstate.tag}"
    cicd_buildstate['useQualityGate'] = env.useQualityGate ?: true
    cicd_buildstate['abortIfQualityGateFail'] = env.abortIfQualityGateFail ?: true
    cicd_buildstate['buildUrlMd'] = '[' + jobName() + ' ' + currentBuild.displayName.replace('[', '\\[') + '](' + env.BUILD_URL + ')'
    cicd_buildstate['submitter'] = env.submitter.tokenize(',') ?: []
    cicd_buildstate['recipients'] = cicd_buildstate.submitter.findAll { it.startsWith('@') || it.startsWith('~') } ?: null
    cicd_buildstate['gitAuthor'] = gitAuthor
    cicd_buildstate['gitEmail'] = gitEmail

    currentBuild.displayName = cicd_buildstate.currentBuild.displayName

    cicd_log.INFO('Contents of cicd_buildstate-object:')
    cicd_buildstate.keys.each { entry -> println entry + " -> " + cicd_buildstate[entry]}

    return cicd_buildstate
}
