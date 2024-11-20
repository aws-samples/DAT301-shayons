# DAT301 - Build Generative AI powered search with Amazon Aurora and Amazon RDS - AWS re:Invent 2024

Welcome to DAT301! The integration of embeddings generated from LLMs for [Amazon Aurora PostgreSQL-Compatible Edition](https://aws.amazon.com/rds/aurora/) and [Amazon RDS for PostgreSQL](https://aws.amazon.com/rds/postgresql/) presents a powerful and efficient solution for optimizing the product catalog similarity search experience. By using foundation models and vector embeddings, businesses can enhance the accuracy and speed of similarity searches by using [Retrieval Augmented Generation (RAG)](https://aws.amazon.com/what-is/retrieval-augmented-generation/), which ultimately leads to improved user satisfaction and a more personalized experience.

<!--![Workshop Banner](static/dat301_intro.png)-->

## Workshop Overview

In this workshop, you'll explore building GenAI-powered e-commerce solutions using a fictitious company called **Blaize Bazaar**.

## Learning Objectives
- Integrate foundation models with e-commerce data for product insights
- Build generative AI-powered product recommendations
- Analyze shopping trends using vector embeddings
- Create personalized customer experiences
- Streamline operations (customer support and inventory management) using Amazon Bedrock Knowledge Bases and Amazon Bedrock Agents

## Dataset

This workshop uses a subset of the Amazon Products Dataset (2023), which contains information about 21,704 Amazon products collected in January 2023. 

Dataset Details:
- Source: [Amazon Products Dataset 2023 (21,704 Products)](https://www.kaggle.com/datasets/asaniczka/amazon-products-dataset-2023-1-4m-products)
- Asaniczka. (2023). Amazon Products Dataset 2023 (1.4M Products) [Data set]. Kaggle. https://doi.org/10.34740/KAGGLE/DS/3798081

## Prerequisites

Before starting this workshop, you should have:
- An AWS Account with admin access
- Basic understanding of PostgreSQL and Python

## Getting Started

Please follow the lab guide used for the workshop to get started.

## Security Considerations

This workshop environment is designed for learning and should not be used for production workloads. Consider the following security notes:

- Sample data is used and contains no sensitive information
- IAM roles are created with workshop-specific permissions
- All resources should be deleted after workshop completion

## Clean Up

To avoid ongoing charges, delete all workshop resources.

## Additional Resources

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Claude API Documentation](https://www.anthropic.com/amazon-bedrock)
- [AWS Bedrock Documentation](https://aws.amazon.com/bedrock/claude/)
- [Anthropic Prompt Engineering Documentation](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Bedrock Agents Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)

## Contributing

We welcome contributions! Please see our [contribution guidelines](CONTRIBUTING.md) for details.

## License

This workshop is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

The Amazon Products Dataset used in this workshop is subject to Kaggle's database licensing terms and Alexander Saniczka's usage terms. Please refer to the [dataset page](https://www.kaggle.com/datasets/asaniczka/amazon-products-dataset-2023-1-4m-products) for complete licensing information.

## Support & Feedback

If you discover a potential security issue, please notify AWS Security rather than opening a public issue. For other problems or suggestions:

1. Open a GitHub issue
2. Provide detailed description of the problem
3. Include steps to reproduce if applicable

## Authors & Acknowledgments

- Shayon Sanyal, Principal WW PostgreSQL Specialist SA, AWS

---
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
