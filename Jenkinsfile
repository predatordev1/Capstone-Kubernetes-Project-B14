pipeline {
    agent any

    environment {
        // AWS Configuration
        AWS_REGION      = 'us-west-1'
        AWS_ACCOUNT_ID  = '975050024946'
        ECR_REGISTRY    = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

        // Short commit hash used as the immutable image tag for this build
        // Using latest alone means you can never reliably roll back — commit hash fixes that
        GIT_COMMIT_SHORT = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()

        // ECR image names — ALL with -pp suffix to avoid conflicts in the shared AWS account
        AUTH_IMAGE      = "${ECR_REGISTRY}/streamingapp-auth-pp"
        STREAMING_IMAGE = "${ECR_REGISTRY}/streamingapp-streaming-pp"
        ADMIN_IMAGE     = "${ECR_REGISTRY}/streamingapp-admin-pp"
        CHAT_IMAGE      = "${ECR_REGISTRY}/streamingapp-chat-pp"
        FRONTEND_IMAGE  = "${ECR_REGISTRY}/streamingapp-frontend-pp"
        HEALING_IMAGE   = "${ECR_REGISTRY}/streamingapp-healing-controller-pp"

        // The nginx ingress ELB hostname — public URL browsers use to reach the app
        // React is built at compile time (REACT_APP_* vars are baked into the JS bundle)
        // HTTP API calls use relative paths (/api/auth etc.) — no hardcoded host needed
        // Only WebSocket and streaming public URL need the absolute hostname
        NGINX_URL = 'http://k8s-ingressn-ingressn-c9769de705-60586d08c9ac6f4d.elb.us-west-1.amazonaws.com'

        // EKS cluster name
        EKS_CLUSTER = 'streamingapp-cluster-pp'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
                sh 'git rev-parse --short HEAD'
            }
        }

        stage('Build Docker Images') {
            parallel {
                stage('Build Auth Service') {
                    steps {
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
                        dir('frontend') {
                            // WHY relative paths for API URLs:
                            // React runs in the USER'S BROWSER, not inside Kubernetes.
                            // The browser cannot resolve "auth-service:3001" (k8s internal DNS).
                            // Using /api/auth means the browser sends the request to the same
                            // origin as the page (the nginx ELB URL), and nginx routes it to
                            // the correct backend pod. This is the correct pattern.
                            //
                            // WHY NGINX_URL is still needed for CHAT_SOCKET_URL + STREAMING_PUBLIC_URL:
                            // Socket.IO requires an absolute URL for the WebSocket handshake.
                            // STREAMING_PUBLIC_URL is used to construct video streaming endpoints.
                            sh """
                                docker build \
                                  --build-arg REACT_APP_AUTH_API_URL=/api/auth \
                                  --build-arg REACT_APP_STREAMING_API_URL=/api/streaming \
                                  --build-arg REACT_APP_STREAMING_PUBLIC_URL=${NGINX_URL} \
                                  --build-arg REACT_APP_ADMIN_API_URL=/api/admin \
                                  --build-arg REACT_APP_CHAT_API_URL=/api/chat \
                                  --build-arg REACT_APP_CHAT_SOCKET_URL=${NGINX_URL} \
                                  -t ${FRONTEND_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${FRONTEND_IMAGE}:${GIT_COMMIT_SHORT} ${FRONTEND_IMAGE}:latest
                            """
                        }
                    }
                }

                stage('Build Healing Controller') {
                    steps {
                        dir('healing-controller') {
                            sh """
                                docker build -t ${HEALING_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${HEALING_IMAGE}:${GIT_COMMIT_SHORT} ${HEALING_IMAGE}:latest
                            """
                        }
                    }
                }
            }
        }

        stage('Login to ECR') {
            steps {
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
                        sh """
                            docker push ${AUTH_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${AUTH_IMAGE}:latest
                        """
                    }
                }
                stage('Push Streaming') {
                    steps {
                        sh """
                            docker push ${STREAMING_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${STREAMING_IMAGE}:latest
                        """
                    }
                }
                stage('Push Admin') {
                    steps {
                        sh """
                            docker push ${ADMIN_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${ADMIN_IMAGE}:latest
                        """
                    }
                }
                stage('Push Chat') {
                    steps {
                        sh """
                            docker push ${CHAT_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${CHAT_IMAGE}:latest
                        """
                    }
                }
                stage('Push Frontend') {
                    steps {
                        sh """
                            docker push ${FRONTEND_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${FRONTEND_IMAGE}:latest
                        """
                    }
                }
                stage('Push Healing Controller') {
                    steps {
                        sh """
                            docker push ${HEALING_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${HEALING_IMAGE}:latest
                        """
                    }
                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                // Jenkins EC2 has the StreamingApp-EC2-Role instance profile
                // That role is in aws-auth ConfigMap as system:masters — no extra credentials needed
                sh """
                    aws eks update-kubeconfig --name ${EKS_CLUSTER} --region ${AWS_REGION}
                    helm upgrade --install streamingapp-pp helm/streamingapp/ \
                      --namespace default \
                      --set image.tag=${GIT_COMMIT_SHORT} \
                      --timeout 10m \
                      --atomic
                """
            }
        }

        stage('Cleanup') {
            steps {
                // Remove local images — they are safely stored in ECR
                sh 'docker system prune -af --volumes'
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded — deployed commit ${GIT_COMMIT_SHORT} to EKS"
        }
        failure {
            echo 'Pipeline failed — check stage logs above'
        }
    }
}
