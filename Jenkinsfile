pipeline {
    agent any

    options {
        timestamps()
        ansiColor('xterm')
    }
    
    triggers {
        githubPush()
    }

    environment {
        COMPOSE_FILE = 'docker-compose.yml'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    parameters {
        string(name: 'AZURE_VAULT_NAME', defaultValue: 'my-django-vault', description: 'Azure Key Vault name containing SECRET_KEY and DB_PASSWORD/DB-PASS secrets')
        string(name: 'ALLOWED_HOSTS', defaultValue: '*', description: 'Comma-separated Django ALLOWED_HOSTS')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Containers') {
            steps {
                sh 'docker-compose -f ${COMPOSE_FILE} build --pull'
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    docker-compose -f ${COMPOSE_FILE} run --rm \
                      -e ENV=CI \
                      -e DEBUG=False \
                      -e SECRET_KEY=jenkins_test_secret \
                      -e CELERY_BROKER_URL=redis://redis:6379/0 \
                      web sh -c "if [ -f manage.py ]; then \
                        python manage.py test; \
                      elif [ -f task_manager/manage.py ]; then \
                        python task_manager/manage.py test; \
                      else \
                        echo 'ERROR: manage.py not found. Checked ./manage.py and ./task_manager/manage.py' >&2; \
                        find /app -maxdepth 5 -name manage.py -print || true; \
                        exit 1; \
                      fi"
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    export AZURE_VAULT_NAME=${AZURE_VAULT_NAME}
                    export ALLOWED_HOSTS=${ALLOWED_HOSTS}

                    # For Azure VM with Managed Identity, this enables Key Vault auth for DefaultAzureCredential.
                    az login --identity || true

                    docker-compose -f ${COMPOSE_FILE} up -d --remove-orphans
                    docker-compose -f ${COMPOSE_FILE} ps
                '''
                echo 'Deployment successful.'
            }
        }
    }

    post {
        always {
            sh 'docker-compose -f ${COMPOSE_FILE} ps || true'
        }
        success {
            echo 'Pipeline completed successfully!'
        }
    }
}