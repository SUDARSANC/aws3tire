pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify Project') {
            steps {
                sh 'echo "FoodHub project checked out successfully"'
                sh 'ls -la'
            }
        }
    }

    post {
        success {
            echo 'FoodHub Pipeline completed successfully!'
        }
        failure {
            echo 'FoodHub Pipeline failed.'
        }
    }
}
