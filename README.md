# Unauthenticated-Gitlab-DoS
Unauthenticated Gitlab DoS - Uncontrolled Resource Consumption - 8vCPU &amp; 16GB RAM GCP Instance OOM Crash

## Quick Start

1. Clone the repository:
```
git clone https://github.com/justas-b1/Unauthenticated-Gitlab-DoS.git
cd Unauthenticated-Gitlab-DoS
```

2. Run
```
python lfs.py --domain https://your-gitlab-domain.com
```

## Video POC

https://www.youtube.com/watch?v=VGsuyPKELqo

[![PoC Video](https://img.youtube.com/vi/VGsuyPKELqo/maxresdefault.jpg)](https://youtu.be/VGsuyPKELqo)

## Command-Line Arguments

| Argument  | Description | Default Value |
| ------------- | ------------- | ------------- |
| --domain  | Target GitLab instance URL  | https://c40b-88-222-161-135.ngrok-free.app |
| --file_name  | Payload file  | lfs_payload_3mb.json |
| --threads  | Total Number of Threads | 7 |
| --delay  | Limits new thread creation - 1 is 1 RPS, 0.5 is 2RPS, etc.  | 1 |

## Code Explanation

`generate_lfs_objects(n)`

Generates n dummy LFS objects with sequential fake OIDs (SHA256 hashes).

`create_payload_file(file_name)`

Creates a JSON payload (e.g., lfs_payload_3mb.json) with LFS batch request data. This is useful if you don't want to regenerate payload every run.

`discover_lfs_endpoint(domain)`

Uses curl to fetch the LFS API endpoint from a GitLab instance’s public projects.

`send_test_request(payload_file, lfs_endpoint)`

Sends a test request and checks for HTTP 413 Payload Too Large errors. This is for these edge cases where maximum accepted body size is 1MB.

`send_curl_request(thread_num, payload_file, lfs_endpoint)`

Threaded function to send payloads to LFS endpoint.

## ⚠️ Legal Disclaimer  
This Proof-of-Concept (PoC) is provided **for educational purposes only**.  

- **Authorized Use Only**: Test only on systems you own or have explicit permission to assess.  
- **No Liability**: The author is not responsible for misuse or damages caused by this tool.  
- **Ethical Responsibility**: Do not use this tool to violate laws or exploit systems without consent.  

By using this software, you agree to these terms. 

Gitlab doesn't accept 99.9% of DoS vulnerabilities. This vulnerability is out-of-scope unfortunately :(.

`DoS vulnerabilities caused by unlimited input fields`

Out-of-scope bugs are useless noise (🗑️) — they waste time chasing irrelevant issues that don’t impact the actual target, like reporting a typo in a login page’s footer. They distract from real threats, clog reports with garbage, and show you didn’t bother reading the rules.

Submitting them is like demanding a refund for a sandwich you didn’t order.
