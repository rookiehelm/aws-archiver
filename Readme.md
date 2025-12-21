pipeline {
    agent none

    parameters {
        choice(
            name: 'YEARS',
            choices: ['1', '2', '3', '4', '5'],
            description: 'Archive images older than N years'
        )
    }

    stages {
        stage('ECR Archive Parallel') {
            parallel {
                stage('Server-0') {
                    agent { label 'server-0' }
                    steps {
                        sh "bash ecr_archiver.sh ${params.YEARS} 0"
                    }
                }

                stage('Server-1') {
                    agent { label 'server-1' }
                    steps {
                        sh "bash ecr_archiver.sh ${params.YEARS} 1"
                    }
                }

                stage('Server-2') {
                    agent { label 'server-2' }
                    steps {
                        sh "bash ecr_archiver.sh ${params.YEARS} 2"
                    }
                }

                stage('Server-3') {
                    agent { label 'server-3' }
                    steps {
                        sh "bash ecr_archiver.sh ${params.YEARS} 3"
                    }
                }
            }
        }
    }
}
