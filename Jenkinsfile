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
        string(name: 'ALLOWED_HOSTS', defaultValue: '', description: 'Optional override. Comma-separated Django ALLOWED_HOSTS (for example: your-domain.com,www.your-domain.com,4.186.40.170)')
        string(name: 'NGINX_HOST_PORT', defaultValue: '8081', description: 'Host port mapped to nginx container port 80')
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
                sh '''
                    set -eu
                    if command -v docker-compose >/dev/null 2>&1; then
                      COMPOSE_CMD='docker-compose'
                    elif docker compose version >/dev/null 2>&1; then
                      COMPOSE_CMD='docker compose'
                    else
                      echo 'ERROR: Neither docker-compose nor docker compose is available on this Jenkins agent.' >&2
                      exit 1
                    fi
                    ${COMPOSE_CMD} -f ${COMPOSE_FILE} build --pull
                '''
            }
        }

        stage('Run Tests') {
            steps {
                dir("${SOURCE_DIR}") {
                    sh '''
                    set -eu
                        if command -v docker-compose >/dev/null 2>&1; then
                          COMPOSE_CMD='docker-compose'
                        elif docker compose version >/dev/null 2>&1; then
                          COMPOSE_CMD='docker compose'
                        else
                          echo 'ERROR: Neither docker-compose nor docker compose is available on this Jenkins agent.' >&2
                          exit 1
                        fi

                        ${COMPOSE_CMD} -f ${COMPOSE_FILE} run --rm \
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
                        string(credentialsId: 'SECRET_KEY', variable: 'SECRET_KEY'),
                        string(credentialsId: 'DB_HOST', variable: 'DB_HOST'),
                        string(credentialsId: 'DB_NAME', variable: 'DB_NAME'),
                        string(credentialsId: 'DB_USER', variable: 'DB_USER'),
                        string(credentialsId: 'DB_PASS', variable: 'DB_PASS'),
                        string(credentialsId: 'DB_PORT', variable: 'DB_PORT'),
                        string(credentialsId: 'AZURE_STORAGE_CONNECTION_STRING', variable: 'AZURE_STORAGE_CONNECTION_STRING'),
                        string(credentialsId: 'USE_AZURE_SQL', variable: 'USE_AZURE_SQL'),
                        string(credentialsId: 'AZURE_ACCOUNT_NAME', variable: 'AZURE_ACCOUNT_NAME'),
                        string(credentialsId: 'AZURE_ACCOUNT_KEY', variable: 'AZURE_ACCOUNT_KEY')
                    ]) {
                        sh '''
                            set -eu

                            if command -v docker-compose >/dev/null 2>&1; then
                              COMPOSE_CMD='docker-compose'
                            elif docker compose version >/dev/null 2>&1; then
                              COMPOSE_CMD='docker compose'
                            else
                              echo 'ERROR: Neither docker-compose nor docker compose is available on this Jenkins agent.' >&2
                              exit 1
                            fi

                        export ALLOWED_HOSTS="${ALLOWED_HOSTS:-}"
                        export USE_AZURE_SQL="${USE_AZURE_SQL:-True}"
                        export NGINX_HOST_PORT="${NGINX_HOST_PORT:-8081}"

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
                              ${COMPOSE_CMD} -f ${COMPOSE_FILE} down --remove-orphans || true
                            fi

                            if [ -z "${ALLOWED_HOSTS}" ]; then
                              PRIMARY_HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
                              ALLOWED_HOSTS="localhost,127.0.0.1"
                              if [ -n "${PRIMARY_HOST_IP}" ]; then
                                ALLOWED_HOSTS="${ALLOWED_HOSTS},${PRIMARY_HOST_IP}"
                              fi
                              export ALLOWED_HOSTS
                              echo "ALLOWED_HOSTS was empty. Falling back to: ${ALLOWED_HOSTS}" >&2
                              echo "Set the ALLOWED_HOSTS parameter to your public domain/IP for production." >&2
                            fi

                            if [ "${ALLOWED_HOSTS}" = "*" ]; then
                              echo "ERROR: ALLOWED_HOSTS cannot be '*'." >&2
                              echo "Example: ALLOWED_HOSTS=your-domain.com,www.your-domain.com,4.186.40.170" >&2
                              exit 1
                            fi

                            if command -v ss >/dev/null 2>&1 && ss -ltn "sport = :${NGINX_HOST_PORT}" | grep -q LISTEN; then
                            echo "ERROR: Requested host port ${NGINX_HOST_PORT} is already in use." >&2
                              echo "Set NGINX_HOST_PORT to a free port and open that port in your NSG/firewall." >&2
                              exit 1
                            fi

                            ${COMPOSE_CMD} -f ${COMPOSE_FILE} up -d --remove-orphans
                            ${COMPOSE_CMD} -f ${COMPOSE_FILE} ps

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
                sh '''
                    set +e
                    if command -v docker-compose >/dev/null 2>&1; then
                      docker-compose -f ${COMPOSE_FILE} ps
                    elif docker compose version >/dev/null 2>&1; then
                      docker compose -f ${COMPOSE_FILE} ps
                    fi
                    true
                '''
            }
        }
        success {
            echo 'Pipeline completed successfully!'
        }
    }
}
