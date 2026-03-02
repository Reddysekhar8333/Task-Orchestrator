pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
        ansiColor('xterm')
    }
    
    triggers {
        githubPush()
    }

    environment {
        COMPOSE_FILE = 'docker-compose.yml'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        SOURCE_DIR = "src-${env.BUILD_NUMBER}"
        COMPOSE_PROJECT_NAME = 'task-orchestrator'
    }

    parameters {
        string(name: 'ALLOWED_HOSTS', defaultValue: '*', description: 'Comma-separated Django ALLOWED_HOSTS')
        string(name: 'NGINX_HOST_PORT', defaultValue: '8080', description: 'Host port mapped to nginx container port 80')
    }

    stages {
        stage('Prepare workspace'){
            steps {
                sh '''
                    # Some previous Docker runs can leave root-owned files/directories in
                    # the Jenkins workspace, which breaks SCM checkout on the next build.
                    if command -v docker >/dev/null 2>&1; then
                      docker run --rm -v "${WORKSPACE}:/workspace" alpine:3.20 \
                        sh -c "chown -R $(id -u):$(id -g) /workspace" || true
                    fi

                    # Defensive cleanup for the path that previously blocked checkout.
                    if [ -d "${WORKSPACE}/nginx/default.conf" ]; then
                      chmod -R u+w "${WORKSPACE}/nginx/default.conf" || true
                      rm -rf "${WORKSPACE}/nginx/default.conf" || true
                    fi
                '''
                deleteDir()
            }
        }

        stage('Checkout') {
            steps {
                //checkout scm
                checkout scm
                dir("${SOURCE_DIR}") {
                    checkout scm
                }
            }
        }

        stage('Build Containers') {
            steps {
                sh 'docker-compose -f ${COMPOSE_FILE} build --pull'
            }
        }

        stage('Run Tests') {
            steps {
                dir("${SOURCE_DIR}") {
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
        }

        stage('Deploy') {
            steps {
                dir("${SOURCE_DIR}") {
                    withCredentials([
                        string(credentialsId: 'task-orchestrator-secret-key', variable: 'SECRET_KEY'),
                        string(credentialsId: 'task-orchestrator-db-host', variable: 'DB_HOST'),
                        string(credentialsId: 'task-orchestrator-db-name', variable: 'DB_NAME'),
                        string(credentialsId: 'task-orchestrator-db-user', variable: 'DB_USER'),
                        string(credentialsId: 'task-orchestrator-db-pass', variable: 'DB_PASS'),
                        string(credentialsId: 'task-orchestrator-azure-storage-connection-string', variable: 'AZURE_STORAGE_CONNECTION_STRING')
                    ]) {
                        sh '''
                            set -eu

                        export ALLOWED_HOSTS=${ALLOWED_HOSTS}
                        export USE_AZURE_SQL=${USE_AZURE_SQL:-True}
                        export NGINX_HOST_PORT=${NGINX_HOST_PORT:-8080}

                        REQUIRED_ENV_VARS="SECRET_KEY DB_HOST DB_NAME DB_USER DB_PASS AZURE_STORAGE_CONNECTION_STRING"
                            for VAR_NAME in ${REQUIRED_ENV_VARS}; do
                              VAR_VALUE=$(printenv "${VAR_NAME}" || true)
                              if [ -z "${VAR_VALUE}" ]; then
                                echo "ERROR: Required environment variable ${VAR_NAME} is missing or empty."
                                echo "Ensure Jenkins Credentials are configured with the expected credential IDs."
                                exit 1
                              fi
                            done
                            
                            if docker ps --format '{{.Names}}' | grep -q '^task-orchestrator-'; then
                              echo "Stopping existing task-orchestrator containers before redeploy..."
                              docker-compose -f ${COMPOSE_FILE} down --remove-orphans || true
                            fi

                            if command -v ss >/dev/null 2>&1 && ss -ltn "sport = :${NGINX_HOST_PORT}" | grep -q LISTEN; then
                            echo "Requested host port ${NGINX_HOST_PORT} is already in use. Searching for an available port..."
                            CANDIDATE_PORT=${NGINX_HOST_PORT}
                            while ss -ltn "sport = :${CANDIDATE_PORT}" | grep -q LISTEN; do
                                CANDIDATE_PORT=$((CANDIDATE_PORT + 1))
                            done
                            export NGINX_HOST_PORT=${CANDIDATE_PORT}
                            echo "Using fallback host port ${NGINX_HOST_PORT} for nginx."
                            fi

                            docker-compose -f ${COMPOSE_FILE} up -d --remove-orphans
                            docker-compose -f ${COMPOSE_FILE} ps
                    '''
                    echo 'Deployment successful.'
                    }
                }
            }
        }
    }
    post {
        always {
            dir("${SOURCE_DIR}") {
                sh 'docker-compose -f ${COMPOSE_FILE} ps || true'
            }
        }
        success {
            echo 'Pipeline completed successfully!'
        }
    }
}
