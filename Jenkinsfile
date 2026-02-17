pipeline {
    agent any
    
    environment {
        // AWS Configuration
        AWS_REGION = 'us-west-1'
        AWS_ACCOUNT_ID = '975050024946'
        ECR_REGISTRY = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        
        // Get short commit hash for image tagging
        GIT_COMMIT_SHORT = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
        
        // Image names
        AUTH_IMAGE = "${ECR_REGISTRY}/streamingapp-auth"
        STREAMING_IMAGE = "${ECR_REGISTRY}/streamingapp-streaming"
        ADMIN_IMAGE = "${ECR_REGISTRY}/streamingapp-admin"
        CHAT_IMAGE = "${ECR_REGISTRY}/streamingapp-chat"
        FRONTEND_IMAGE = "${ECR_REGISTRY}/streamingapp-frontend"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '📥 Checking out code...'
                checkout scm
                sh 'git rev-parse --short HEAD'
            }
        }
        
        stage('Build Docker Images') {
            parallel {
                stage('Build Auth Service') {
                    steps {
                        echo '🔨 Building Auth Service...'
                        dir('backend/authService') {
                            sh """
                                docker build -t ${AUTH_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${AUTH_IMAGE}:${GIT_COMMIT_SHORT} ${AUTH_IMAGE}:latest
                            """
                        }
                    }
                }
                
                stage('Build Streaming Service') {
                    steps {
                        echo '🔨 Building Streaming Service...'
                        dir('backend/streamingService') {
                            sh """
                                docker build -t ${STREAMING_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${STREAMING_IMAGE}:${GIT_COMMIT_SHORT} ${STREAMING_IMAGE}:latest
                            """
                        }
                    }
                }
                
                stage('Build Admin Service') {
                    steps {
                        echo '🔨 Building Admin Service...'
                        dir('backend/adminService') {
                            sh """
                                docker build -t ${ADMIN_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${ADMIN_IMAGE}:${GIT_COMMIT_SHORT} ${ADMIN_IMAGE}:latest
                            """
                        }
                    }
                }
                
                stage('Build Chat Service') {
                    steps {
                        echo '🔨 Building Chat Service...'
                        dir('backend/chatService') {
                            sh """
                                docker build -t ${CHAT_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${CHAT_IMAGE}:${GIT_COMMIT_SHORT} ${CHAT_IMAGE}:latest
                            """
                        }
                    }
                }
                
                stage('Build Frontend') {
                    steps {
                        echo '🔨 Building Frontend...'
                        dir('frontend') {
                            sh """
                                docker build \
                                  --build-arg REACT_APP_AUTH_API_URL=http://auth-service:3001/api \
                                  --build-arg REACT_APP_STREAMING_API_URL=http://streaming-service:3002/api \
                                  --build-arg REACT_APP_STREAMING_PUBLIC_URL=http://streaming-service:3002 \
                                  --build-arg REACT_APP_ADMIN_API_URL=http://admin-service:3003/api/admin \
                                  --build-arg REACT_APP_CHAT_API_URL=http://chat-service:3004/api/chat \
                                  --build-arg REACT_APP_CHAT_SOCKET_URL=http://chat-service:3004 \
                                  -t ${FRONTEND_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${FRONTEND_IMAGE}:${GIT_COMMIT_SHORT} ${FRONTEND_IMAGE}:latest
                            """
                        }
                    }
                }
            }
        }
        
        stage('Login to ECR') {
            steps {
                echo '🔐 Logging into AWS ECR...'
                sh """
                    aws ecr get-login-password --region ${AWS_REGION} | \
                    docker login --username AWS --password-stdin ${ECR_REGISTRY}
                """
            }
        }
        
        stage('Push Images to ECR') {
            parallel {
                stage('Push Auth') {
                    steps {
                        echo '📤 Pushing Auth Service to ECR...'
                        sh """
                            docker push ${AUTH_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${AUTH_IMAGE}:latest
                        """
                    }
                }
                
                stage('Push Streaming') {
                    steps {
                        echo '📤 Pushing Streaming Service to ECR...'
                        sh """
                            docker push ${STREAMING_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${STREAMING_IMAGE}:latest
                        """
                    }
                }
                
                stage('Push Admin') {
                    steps {
                        echo '📤 Pushing Admin Service to ECR...'
                        sh """
                            docker push ${ADMIN_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${ADMIN_IMAGE}:latest
                        """
                    }
                }
                
                stage('Push Chat') {
                    steps {
                        echo '📤 Pushing Chat Service to ECR...'
                        sh """
                            docker push ${CHAT_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${CHAT_IMAGE}:latest
                        """
                    }
                }
                
                stage('Push Frontend') {
                    steps {
                        echo '📤 Pushing Frontend to ECR...'
                        sh """
                            docker push ${FRONTEND_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${FRONTEND_IMAGE}:latest
                        """
                    }
                }
            }
        }
        
        stage('Cleanup') {
            steps {
                echo '🧹 Cleaning up local Docker images...'
                sh """
                    docker system prune -af --volumes
                """
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline completed successfully!'
            echo "Images tagged with: ${GIT_COMMIT_SHORT} and latest"
        }
        failure {
            echo '❌ Pipeline failed!'
        }
        always {
            echo '📊 Build finished'
        }
    }
}