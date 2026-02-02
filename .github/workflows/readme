## 🎯 Overview

This research project introduces **A Marketplace for Edge Federated ML**, addressing critical challenges in building federated machine learning ecosystems where multiple stakeholders—data providers, model consumers, and service providers—collaborate while preserving data privacy and ensuring transparent quality of training.

### 🌟 Research Highlights

Our work tackles fundamental problems in federated learning marketplaces:

- **Explainable Quality of Training (eQoT)**: A comprehensive framework to measure and explain training quality based on data quality and individual contributions from distributed data sources
- **Privacy-Preserving Mechanisms**: Data remains at the edge with selective trust models
- **Real-time Cost & Quality Monitoring**: Multi-dimensional cost models with transparent evaluation
- **Data Integrity Detection**: Novel approaches to detect malicious data modifications in marketplace settings
- **Asynchronous Training**: Efficient federated learning with bidirectional model aggregation

### 🏗️ Core Components

The research encompasses several interconnected systems:

1. **EADRAN Platform**: Edge marketplAce for DistRibuted AI/ML traiNing
2. **ASYN2F Framework**: ASYNchronous Federated learning Framework with bidirectional aggregation
3. **Data Modification Detection**: Mechanisms to identify fraudulent data changes
4. **Cost & Quality Models**: Comprehensive evaluation frameworks for federated ML

---

## 🚀 Key Features

### 1. **Explainable Quality of Training (eQoT)**

A novel approach to provide transparency and explainability in federated ML training:

**Quality of Data (QoD) Metrics:**
- Class overlap and class parity
- Label purity and feature correlation
- Feature relevance and completeness
- Market context and compatibility

**Contribution Analysis:**
- Individual data provider contribution tracking
- Real-time performance impact measurement
- Dynamic cost evaluation based on contribution
- Transparent reward mechanisms

**Multi-dimensional Cost Model:**
```
Total_Cost = Cost_QoD + Cost_Context + Cost_Performance + Cost_Resources

where:
  Cost_QoD       = f(data_quantity, data_quality)
  Cost_Context   = f(market_reputation, compatibility)
  Cost_Performance = f(accuracy_improvement, convergence_rate)
  Cost_Resources = f(CPU, GPU, RAM, Storage, Network)
```

### 2. **Asynchronous Federated Learning (ASYN2F)**

Innovative framework addressing heterogeneity in distributed training:

**Bidirectional Model Aggregation:**
- **Server-side**: Asynchronous aggregation of local models without waiting for stragglers
- **Worker-side**: Mid-epoch aggregation of global model updates to reduce staleness

**Key Advantages:**
- Addresses obsolete information problem
- Handles heterogeneous training workers
- Adaptive learning rate synchronization
- Improved convergence speed and model performance

**Convergence Analysis:**
- Proven convergence rate: O(1/√T) for convex objectives
- Convergence rate: O(1/T) for strongly convex objectives
- Theoretical guarantees with practical effectiveness

### 3. **Data Modification Detection**

Advanced techniques to maintain marketplace integrity:

**Detection Mechanisms:**
- **Weight Movement Analysis**: Measuring Wasserstein distance across model layers
- **Time Series Anomaly Detection**: ARIMA-based behavioral pattern analysis
- **Cross-client Correlation**: Isolation Forest for outlier identification
- **Enhanced Monitoring**: Comprehensive feature engineering for detection

**Capabilities:**
- Detect synthetic data injection
- Identify dataset replacement
- Recognize data processing manipulation
- Handle privacy-preserving techniques (Differential Privacy, MPC)

### 4. **Edge-Cloud Architecture**

Scalable and practical implementation design:

**Edge Sites:**
- Local data storage and processing
- Containerized training environments
- Resource monitoring and reporting
- Privacy-preserving computation

**Cloud Infrastructure:**
- Orchestration and coordination
- Model aggregation services
- Real-time monitoring and analytics
- Cost computation and billing

**Communication:**
- Message queue-based coordination (RabbitMQ, Redis)
- Model storage (MinIO, AWS S3)
- Streaming analytics (Kafka, Spark)
- Visualization (InfluxDB, Grafana)

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Market Consumer (MC)                        │
│                                                                  │
│  ┌──────────────┐      ┌─────────────┐      ┌───────────────┐ │
│  │  Pre-trained │ ──▶  │   Training  │ ──▶  │    Trained    │ │
│  │    Model     │      │   Request   │      │     Model     │ │
│  └──────────────┘      └──────┬──────┘      └───────────────┘ │
└────────────────────────────────┼──────────────────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  Orchestrator   │
                        │   & Federated   │
                        │     Server      │
                        └────────┬────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼────────┐      ┌───────▼────────┐      ┌───────▼────────┐
│  Edge Node 1   │      │  Edge Node 2   │      │  Edge Node N   │
│                │      │                │      │                │
│ ┌────────────┐ │      │ ┌────────────┐ │      │ ┌────────────┐ │
│ │    Data    │ │      │ │    Data    │ │      │ │    Data    │ │
│ │  Provider  │ │      │ │  Provider  │ │      │ │  Provider  │ │
│ │  (Private  │ │      │ │  (Private  │ │      │ │  (Private  │ │
│ │   Data)    │ │      │ │   Data)    │ │      │ │   Data)    │ │
│ └────────────┘ │      │ └────────────┘ │      │ └────────────┘ │
│                │      │                │      │                │
│ ┌────────────┐ │      │ ┌────────────┐ │      │ ┌────────────┐ │
│ │   Local    │ │      │ │   Local    │ │      │ │   Local    │ │
│ │   Model    │ │      │ │   Model    │ │      │ │   Model    │ │
│ │  Training  │ │      │ │  Training  │ │      │ │  Training  │ │
│ └────────────┘ │      │ └────────────┘ │      │ └────────────┘ │
│                │      │                │      │                │
│ ┌────────────┐ │      │ ┌────────────┐ │      │ ┌────────────┐ │
│ │ Monitoring │ │      │ │ Monitoring │ │      │ │ Monitoring │ │
│ │   Probe    │ │      │ │   Probe    │ │      │ │   Probe    │ │
│ └────────────┘ │      │ └────────────┘ │      │ └────────────┘ │
└────────┬───────┘      └────────┬───────┘      └────────┬───────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  QoT Analysis   │
                        │    & Cost       │
                        │   Computation   │
                        └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  Visualization  │
                        │   Dashboard     │
                        └─────────────────┘
```

### Key Components

#### **Marketplace Services**
- **Data Service**: Metadata management, data quality evaluation
- **Training Service**: Orchestration, model aggregation
- **QoT Analysis Service**: Real-time cost and quality computation
- **Monitoring Service**: Metrics collection and visualization

#### **Edge Infrastructure**
- **Orchestration Service**: Receives and executes training tasks
- **Data Processing**: Local data extraction and preparation
- **Model Training**: Containerized execution environments
- **Resource Monitoring**: CPU, GPU, RAM, storage tracking

#### **Communication Layer**
- **Message Queuing**: RabbitMQ for orchestration, Redis for control
- **Streaming**: Kafka for monitoring data, Spark for analytics
- **Storage**: MinIO/S3 for model artifacts

---

## 📚 Publications

This research has resulted in four peer-reviewed publications covering different aspects of federated ML marketplaces:

### 🏆 Published Papers

#### 1. ASYN2F: Asynchronous Federated Learning Framework with Bidirectional Model Aggregation

> **Authors**: Tien-Dung Cao, Nguyen T. Vuong, Thai Q. Le, Hoang V.N. Dao, Tram Truong-Huu  
> **Published**: IEEE Transactions on Emerging Topics in Computing (TETC), Vol. 13, No. 4, October-December 2025  
> **DOI**: [10.1109/TETC.2025.3609004](https://doi.org/10.1109/TETC.2025.3609004)  
> **Pages**: 1618-1632

**Abstract**: In federated learning, the models can be trained synchronously or asynchronously. Many existing works have focused on developing an aggregation method for the server to aggregate multiple local models into the global model with improved performance. They ignore the heterogeneity of the training workers, which causes the delay in the training of the local models, leading to the obsolete information issue. In this paper, we design and develop ASYN2F, an ASYNchronous Federated learning Framework with bidirectional model aggregation. By bidirectional aggregation, ASYN2F, on one hand, allows the server to asynchronously aggregate multiple local models and generate a new global model. On the other hand, it allows the training workers to aggregate the new version of the global model into a local model, which is being optimized even in the middle of a training epoch.

**Key Contributions**:
- Bidirectional aggregation algorithms for server and workers
- Handling obsolete information in asynchronous settings
- Practical implementation with real-time monitoring
- Extensive experiments on CIFAR-10, CIFAR-100, and EMBER datasets

📄 **GitHub Repository**: [https://github.com/soeai/asyn2f](https://github.com/soeai/asyn2f)

---

#### 2. EADRAN: An Edge Marketplace for Federated Learning

> **Authors**: Tien-Dung Cao, Hong-Tri Nguyen, Minh-Tri Nguyen, Tram Truong-Huu, Hong-Linh Truong  
> **Published**: Future Generation Computer Systems, Vol. 175, 2026  
> **DOI**: [10.1016/j.future.2025.108046](https://doi.org/10.1016/j.future.2025.108046)  
> **Pages**: Article 108046

**Abstract**: The proliferation of edge data availability alongside advanced federated and distributed machine learning training techniques calls for new developments of machine learning (ML) with distributed and private edge data providers. Most existing works, however, focus on the development and optimization of federated ML communication and aggregation techniques and under-research the quality of training based on the impact of the quality of data and contributions of distributed data sources from such providers to the building of ML models. In this paper, we introduce an Edge marketplAce for DistRibuted AI/ML traiNing (EADRAN), a comprehensive platform for federated learning (FL) with independent edge data providers. The key distinguishable feature of EADRAN is to enable the explainable quality of training (eQoT) approach based on the quality of data and the contributions of provided data to the target-trained ML models.

**Key Contributions**:
- Conceptual architecture for federated ML marketplaces
- Explainable Quality of Training (eQoT) framework
- Multi-dimensional cost model with four components
- Integration with Flower FL framework for adaptability
- Comprehensive experiments demonstrating eQoT benefits

📄 **GitHub Repository**: [https://github.com/soeai/eadran](https://github.com/soeai/eadran)

---

#### 3. Detecting Data Modification in Marketplace of Federated Learning

> **Authors**: Tien-Dung Cao, Ngan T.T. Pham, Hoang-Duc Le, Binh T. Nguyen  
> **Published**: International Conference on Machine Learning and Cybernetics (ICMLC), Lecture Notes in Networks and Systems, Vol. 1475, 2025  
> **DOI**: [10.1007/978-3-031-94892-3_42](https://doi.org/10.1007/978-3-031-94892-3_42)  
> **Pages**: 568-581

**Abstract**: This paper addresses the challenge of detecting subtle data manipulations in federated learning marketplaces, focusing on synthetically generated datasets introduced by data providers to inflate their contributions' value. We propose a novel approach incorporating enhanced monitoring features and sophisticated analysis of local model weight movements. Our method measures the moving distance of local model weights, applies time series anomaly detection, and analyzes cross-client correlations to distinguish between genuine learning divergence and manipulation attempts.

**Key Contributions**:
- Enhanced monitoring features for malicious behavior detection
- Weight movement analysis using Wasserstein distance
- Time series anomaly detection (ARIMA) combined with correlation analysis
- 100% recall rate in detecting data modification events
- Evaluation on CNN (CIFAR-10) and LSTM (text classification) scenarios

---

#### 4. Enabling Awareness of Quality of Training and Costs in Federated Machine Learning Marketplaces

> **Authors**: Tien-Dung Cao, Hong-Linh Truong, Tram Truong-Huu, Minh-Tri Nguyen  
> **Published**: 15th IEEE/ACM International Conference on Utility and Cloud Computing (UCC), 2022  
> **DOI**: [10.1109/UCC56403.2022.00015](https://doi.org/10.1109/UCC56403.2022.00015)  
> **Pages**: 41-50

**Abstract**: The proliferation of data and machine learning (ML) as a service, coupled with advanced federated and distributed training techniques, fosters the development of federated ML marketplaces. One important, but under-researched, aspect is to enable the stakeholder interactions centered around the quality of training and costs in the marketplace and the service models in federated ML training. This paper conceptualizes a federated ML marketplace and proposes a framework to enable the awareness of the quality of training and a variety of costs where both data providers and ML model consumers can easily value the contribution of each data source to ML model performance in nearly real-time.

**Key Contributions**:
- Conceptualization of federated ML marketplace stakeholders
- Definition of quality of training (QoT) metrics
- Four-component cost model for comprehensive evaluation
- Real-time cost computation and monitoring framework
- Practical experiments demonstrating cost transparency

---

### 📊 Research Impact

**Publication Venues**:
- IEEE TETC (Q1 Journal, Impact Factor: 6.4)
- Future Generation Computer Systems (Q1 Journal, Impact Factor: 7.5)
- IEEE/ACM UCC (Rank A Conference)
- ICMLC (International Conference)

**Research Coverage**:
- Asynchronous federated learning algorithms
- Edge computing and marketplace design
- Data quality assessment and contribution tracking
- Security and data integrity in collaborative ML
- Cost models and real-time monitoring

**Technology Stack**:
- Federated Learning Frameworks: Flower, custom implementations
- Edge Computing: Docker, containerization
- Message Queuing: RabbitMQ, Redis, Kafka
- Storage: MinIO, AWS S3, MongoDB
- Monitoring: Spark Streaming, InfluxDB, Grafana
- ML Frameworks: TensorFlow, PyTorch, scikit-learn

---

## 👥 Research Team

### Principal Investigator

**Tien-Dung Cao, PhD**  
📧 dung.cao@ttu.edu.vn  
🏛️ School of Information Technology, Tan Tao University, Vietnam  
🔬 **Research Interests**: Federated Learning, Edge Computing, Machine Learning Marketplaces, Data Quality, Distributed Systems

**Role**: Project lead, conceptualization, methodology, implementation, and writing

---

### Collaborators

**Hong-Linh Truong, PhD**  
🏛️ Department of Computer Science, Aalto University, Finland  
🔬 **Research Interests**: Cloud Computing, Service Engineering, Data Engineering  
**Contribution**: Conceptual architecture, marketplace design, cost models

**Tram Truong-Huu, PhD, Senior Member IEEE**  
🏛️ Singapore Institute of Technology & Agency for Science, Technology and Research (A*STAR), Singapore  
🔬 **Research Interests**: Cybersecurity, Federated Learning, Distributed Systems  
**Contribution**: Algorithm design, convergence analysis, security aspects

**Binh T. Nguyen**  
🏛️ Faculty of Mathematics, University of Science, VNU-HCMC, Vietnam  
🔬 **Research Interests**: Machine Learning, Computer Vision, and Scientific Computing
**Contribution**: Statistical analysis, methodology
---

### Graduate Students & Research Assistants

**Nguyen T. Vuong**  
🏛️ Aalto University, Finland (Research Intern) & Tan Tao University, Vietnam  
**Contribution**: ASYN2F implementation, experiments, analysis

**Hong-Tri Nguyen**  
🏛️ Aalto University, Finland  
**Contribution**: EADRAN platform development, integration

**Minh-Tri Nguyen**  
🏛️ Aalto University, Finland  
**Contribution**: System implementation, monitoring services

**Thai Q. Le**  
🏛️ Tan Tao University, Vietnam  
**Contribution**: Software development, testing

**Hoang V.N. Dao**  
🏛️ Tan Tao University, Vietnam  
**Contribution**: Implementation, experiments

**Ngan T.T. Pham**  
🏛️ Tan Tao University, Vietnam  
**Contribution**: Data modification detection research

**Hoang-Duc Le**  
🏛️ Faculty of Mathematics, University of Science, VNU-HCMC, Vietnam  
**Contribution**: Anomaly detection algorithms

---

## 🙏 Acknowledgments

This research is supported by:

- **Tan Tao University Foundation for Science and Technology Development**  
  Grant No. TTU.RS.22.102.001

- **CSC IT Center for Science, Finland**  
  Cloud computing resources and infrastructure

- **Aalto University, Finland**  
  Research collaboration and support

- **Singapore Institute of Technology**  
  Research collaboration

We would like to express our gratitude to all students and staff at Tan Tao University who contributed to the implementation and testing of the platforms.

---

## 📜 License

This research project and associated code are released under the MIT License. See individual repositories for specific licensing details.

---

## 📞 Contact & Collaboration

We welcome collaboration opportunities, questions, and feedback:

- **Principal Investigator**: dung.cao@ttu.edu.vn
- **Project Issues**: [GitHub Issues](https://github.com/soeai/eadran/issues)
- **Research Inquiries**: Via email to the principal investigator

---

### Open Source Projects
- 📖 [EADRAN Repository](https://github.com/soeai/eadran)
- 📖 [ASYN2F Repository](https://github.com/soeai/asyn2f)

### Related Frameworks & Tools
- 🌐 [Flower Federated Learning Framework](https://flower.ai/)
- 🌐 [OpenFL](https://www.openfl.org/)
- 🌐 [FedML](https://fedml.ai/)

---

<div align="center">
  <h3>🌟 Research in Federated Machine Learning Marketplaces 🌟</h3>
  <p>Advancing Privacy-Preserving, Explainable, and Cost-Transparent Machine Learning</p>
  <br>
  <p>
    <a href="https://github.com/soeai/eadran">⭐ Star EADRAN</a> •
    <a href="https://github.com/soeai/asyn2f">⭐ Star ASYN2F</a>
  </p>
  <br>
  <p><i>Made with ❤️ by the Tan Tao University Research Team and International Collaborators</i></p>
</div>
