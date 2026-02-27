pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url:'https://github.com/Reddysekhar8333/Task-Orchestrator.git'
            }
        }
        stage('Build Containers') {
            steps {
                sh 'docker-compose build'
            }
        }
        stage('Run Tests') {
            steps {
                // Jenkins will fail the build here if tests don't pass
                sh 'docker-compose run web python manage.py test'
            }
        }
        stage('Deploy to Azure') {
            steps {
                // Only runs if tests pass
                sh 'docker-compose up -d'
                print "Deployment Successful to Azure VM"
            }
        }
    }
}