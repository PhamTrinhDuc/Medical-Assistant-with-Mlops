pipeline {
  agent any 
  
  options {
    timestamps()
    timeout(time: 1, unit: 'HOURS')
  }
  
  stages {
    stage('Checkout') {
      when {
        branch 'main'
      }
      steps {
        echo 'Checking out source code...'
        checkout scm
      }
    }

    stage('Install Dependencies') {
      when {
        branch 'main'
      }
      steps {
        echo 'Installing dependencies...'
      }
    }

    stage('Lint') {
      when {
        branch 'main'
      }
      steps {
        echo 'Linting code...'
      }
    }

    stage('Test') {
      when {
        branch 'main'
      }
      steps {
        echo 'Running tests...'
      }
    }

    stage('Deploy') {
      when {
        branch 'main'
      }
      steps {
        echo 'Deploying to production...'
        sh 'echo "Deployment completed"'
      }
    }
  }
  
  post {
    always {
      echo 'Pipeline finished'
    }
    success {
      echo 'Pipeline succeeded!'
    }
    failure {
      echo 'Pipeline failed!'
    }
  }
}
