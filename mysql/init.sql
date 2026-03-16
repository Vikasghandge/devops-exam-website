
CREATE DATABASE IF NOT EXISTS examdb;
USE examdb;

CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(100) NOT NULL,
    email      VARCHAR(150) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS questions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    question        TEXT NOT NULL,
    options         JSON NOT NULL,
    correct_answer  VARCHAR(10) NOT NULL,
    explanation     TEXT,
    category        VARCHAR(50) DEFAULT 'DevOps'
);

CREATE TABLE IF NOT EXISTS results (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    score      INT NOT NULL,
    total      INT NOT NULL,
    percentage DECIMAL(5,2),
    time_taken INT,
    taken_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO users (username, email, password) VALUES
('Vikas Ghandge', 'vikas@example.com', 'vikas123'),
('Test User',     'test@example.com',  'test123');

INSERT INTO questions (question, options, correct_answer, explanation, category) VALUES

('What is the default network driver used by Docker?',
 '{"A":"host","B":"bridge","C":"overlay","D":"none"}',
 'B',
 'Docker uses the bridge network driver by default. Containers on the same bridge network can communicate with each other.',
 'Docker'),

('Which command shows running Docker containers only?',
 '{"A":"docker ps -a","B":"docker ps","C":"docker ls","D":"docker container show"}',
 'B',
 'docker ps shows only running containers. docker ps -a shows all containers including stopped ones.',
 'Docker'),

('What does the ENTRYPOINT instruction do in a Dockerfile?',
 '{"A":"Sets environment variables","B":"Copies files into image","C":"Defines container executable that always runs","D":"Exposes a port"}',
 'C',
 'ENTRYPOINT defines the main executable that always runs when a container starts. Unlike CMD, it cannot be overridden by arguments.',
 'Docker'),

('Which Kubernetes component assigns pods to nodes?',
 '{"A":"kubelet","B":"kube-proxy","C":"kube-scheduler","D":"etcd"}',
 'C',
 'kube-scheduler watches for new pods and assigns them to appropriate nodes based on resource availability and constraints.',
 'Kubernetes'),

('What is the role of etcd in Kubernetes?',
 '{"A":"Manages container runtime","B":"Stores all cluster state and configuration data","C":"Routes network traffic","D":"Monitors pod health"}',
 'B',
 'etcd is the key-value store that acts as the single source of truth for all cluster data in Kubernetes.',
 'Kubernetes'),

('What does HPA stand for in Kubernetes?',
 '{"A":"High Performance Application","B":"Horizontal Pod Autoscaler","C":"Host Process Agent","D":"Hybrid Pod Architecture"}',
 'B',
 'HPA automatically scales the number of pod replicas based on CPU/memory utilization or custom metrics.',
 'Kubernetes'),

('Which Kubernetes object ensures one pod runs on every node?',
 '{"A":"Deployment","B":"ReplicaSet","C":"StatefulSet","D":"DaemonSet"}',
 'D',
 'DaemonSet ensures that a copy of a pod runs on all (or selected) nodes. Used for node monitoring, log collection etc.',
 'Kubernetes'),

('What is the purpose of a Kubernetes ConfigMap?',
 '{"A":"Store sensitive passwords","B":"Store non-sensitive configuration data","C":"Define resource limits","D":"Manage network policies"}',
 'B',
 'ConfigMap stores non-sensitive configuration as key-value pairs. For sensitive data like passwords, use Secrets instead.',
 'Kubernetes'),

('What does terraform init do?',
 '{"A":"Creates resources on AWS","B":"Initializes working directory and downloads providers","C":"Shows execution plan","D":"Destroys all resources"}',
 'B',
 'terraform init initializes the working directory, downloads required provider plugins and sets up the backend.',
 'Terraform'),

('What is Terraform state used for?',
 '{"A":"Store provider credentials","B":"Track real-world infrastructure managed by Terraform","C":"Run scripts on servers","D":"Generate SSH keys"}',
 'B',
 'Terraform state maps your configuration to real infrastructure resources so Terraform knows what it manages.',
 'Terraform'),

('Which command in Terraform shows what changes will be made without applying them?',
 '{"A":"terraform apply","B":"terraform validate","C":"terraform plan","D":"terraform show"}',
 'C',
 'terraform plan creates an execution plan showing what changes will be made. It does NOT apply any changes.',
 'Terraform'),

('What is the purpose of Docker multi-stage builds?',
 '{"A":"Build images on multiple machines","B":"Run multiple apps in one container","C":"Reduce final image size by separating build and runtime","D":"Push to multiple registries"}',
 'C',
 'Multi-stage builds allow you to use multiple FROM statements. Only the final stage is kept, removing build tools and reducing image size significantly.',
 'Docker'),

('What does kubectl get pods -A show?',
 '{"A":"Pods in default namespace","B":"All pods across all namespaces","C":"All Kubernetes resources","D":"Only running pods"}',
 'B',
 '-A flag (or --all-namespaces) shows pods from every namespace in the cluster.',
 'Kubernetes'),

('Which AWS service is used for container image storage?',
 '{"A":"ECS","B":"ECR","C":"EKS","D":"S3"}',
 'B',
 'ECR (Elastic Container Registry) is AWS managed Docker container image registry. ECS and EKS are compute services.',
 'AWS'),

('What does CrashLoopBackOff mean in Kubernetes?',
 '{"A":"Pod is waiting to be scheduled","B":"Node has no resources","C":"Container keeps crashing and Kubernetes keeps restarting it","D":"Image pull failed"}',
 'C',
 'CrashLoopBackOff means the container starts, crashes, and Kubernetes tries to restart it in a loop with increasing backoff delays.',
 'Kubernetes'),

('Which Ansible module is used to install packages on Ubuntu?',
 '{"A":"yum","B":"package","C":"apt","D":"install"}',
 'C',
 'The apt module manages packages on Debian/Ubuntu systems. The yum module is used for RHEL/CentOS systems.',
 'Ansible'),

('What is a Kubernetes namespace used for?',
 '{"A":"Network isolation between clouds","B":"Logical separation of resources within a cluster","C":"Separating master and worker nodes","D":"Container image versioning"}',
 'B',
 'Namespaces provide logical isolation of resources within a single cluster. Useful for separating environments like dev/staging/prod.',
 'Kubernetes'),

('What is the difference between docker stop and docker kill?',
 '{"A":"No difference","B":"docker stop sends SIGTERM (graceful), docker kill sends SIGKILL (force)","C":"docker kill is slower","D":"docker stop deletes the container"}',
 'B',
 'docker stop sends SIGTERM allowing the app to shutdown gracefully with a 10s timeout. docker kill sends SIGKILL immediately.',
 'Docker'),

('Which Terraform command removes a resource from state without destroying it?',
 '{"A":"terraform delete","B":"terraform remove","C":"terraform state rm","D":"terraform destroy -target"}',
 'C',
 'terraform state rm removes a resource from Terraform state without destroying the actual infrastructure.',
 'Terraform'),

('What does a Kubernetes liveness probe do?',
 '{"A":"Checks if pod has enough memory","B":"Determines if container should receive traffic","C":"Restarts container if it becomes unhealthy","D":"Monitors CPU usage"}',
 'C',
 'Liveness probe checks if a container is alive. If it fails, kubelet restarts the container. Readiness probe controls traffic routing.',
 'Kubernetes');
