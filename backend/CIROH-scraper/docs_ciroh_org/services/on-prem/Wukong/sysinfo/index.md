---
title: System Architecture
source: https://docs.ciroh.org/docs/services/on-prem/Wukong/sysinfo
scraped_date: 2025-01-31
---

### Comupute Node

| Compute Node Specifications |
| --- |
| Model | Intel(R) Xeon(R) Platinum 8470 |
| Number of nodes | 1 |
| Sockets per node | 2 |
| Cores per socket | 52 |
| Cores per node | 208 |
| Hardware threads per core | 2 |
| Hardware threads per node | 416 |
| Clock rate | 2.00GHz (3.80GHz max boost) |
| RAM | 1024 GB DDR5-4800 |
| Cache | L1d cache: 4.9 MiB (104 instances)                   <br>L1i cache: 3.3 MiB (104 instances)<br>L2 cache: 208 MiB (104 instances)<br>L3 cache: 210 MiB (2 instances) |
| Local storage per node | 56 TB |
| Number GPUs per node | 8 |
| GPU model | NVIDIA A100 SXM4 |
| Memory per GPU | 80 GB |

info

Presently, the Wukong operates as a stand-alone, self-contained server, implying that the compute node is the login node.

### Network

The Wukong's all GPUs are fully interconnected with NVIDIA NVLink technology.

- [Comupute Node](https://docs.ciroh.org/docs/services/on-prem/Wukong/sysinfo/#comupute-node)
- [Network](https://docs.ciroh.org/docs/services/on-prem/Wukong/sysinfo/#network)