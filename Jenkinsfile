pipeline {
    agent any

    environment {
        VAULT_NAME = 'my-django-vault'
    }

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
                // We pass a dummy SECRET_KEY here just to satisfy Django during testing
                // --remove-orphans cleans up the "orphan container"
                sh "docker-compose run --rm --remove-orphans -e SECRET_KEY=jenkins_test_key web python manage.py test"
            }
        }

        stage('Deploy to Azure') {
            steps {
                // Here we tell Docker about the Vault Name and turn off Debug
                // This triggers the 'if vault_name:' logic in your settings.py
                sh "AZURE_VAULT_NAME=${VAULT_NAME} DEBUG=False docker-compose up -d --remove-orphans"
                echo "Deployment Successful to Azure VM"
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
        }
    }
}