pipeline {
    agent any
    environment {
        /* Servidor remoto onde o deploy será feito */
        DOCKER_NODE = "assuncao"
        DEPLOY_DIR  = "/dados/docker/producao/niesapi-hml"
        BACKUP_APP = "/backup"
                }
    stages{

         stage('SSH transfer') {
            steps([$class: 'BapSshPromotionPublisherPlugin']) {
                sshPublisher(
                    continueOnError: false, failOnError: true,
                    publishers: [
                        sshPublisherDesc(
                            configName: "$DOCKER_NODE",
                            verbose: true,
                            transfers: [
                                sshTransfer(
                                    execCommand: "touch diogo123.txt"
                                        ),
                                sshTransfer(
                                    sourceFiles: "**",
                                    removePrefix: "",
                                    remoteDirectory: "$DEPLOY_DIR"
                                )
                            ]
                        )
                    ]
                )
            }
        }
        stage('Deploy image') {
            steps([$class: 'BapSshPromotionPublisherPlugin']) {
                sshPublisher(
                    continueOnError: false, failOnError: true,
                    publishers: [
                        sshPublisherDesc(
                            configName: "$DOCKER_NODE",
                            verbose: true,
                            transfers: [
                                sshTransfer(
                            execCommand: "docker stack rm niesapi-hml  && sleep 4 && cd $DEPLOY_DIR/ && bash deploy.sh"
                                ),
                          ]
                        )
                    ]
                )
            }
        }
    }


}
