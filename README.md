# Unauthenticated Gitlab DoS

Uncontrolled Resource Consumption - 8vCPU &amp; 16GB RAM GCP Instance OOM Crash.

Gitlab doesn't accept 99.9% of DoS vulnerabilities. This vulnerability is out-of-scope unfortunately 😔.

`DoS vulnerabilities caused by unlimited input fields`

Out-of-scope bugs are useless noise (🗑️) — they waste time chasing irrelevant issues that don’t impact the actual target, like reporting a typo in a login page’s footer. They distract from real threats, clog reports with garbage, and show you didn’t bother reading the rules.

Submitting them is like demanding a refund for a sandwich you didn’t order.

## Video POC

[![PoC Video](https://img.youtube.com/vi/VGsuyPKELqo/maxresdefault.jpg)](https://youtu.be/VGsuyPKELqo)

## Quick Start

1. Clone the repository:
```
git clone https://github.com/justas-b1/Gitlab-DoS.git
cd Gitlab-DoS
```

2. Run
```
python lfs.py --domain https://your-gitlab-domain.com
```

## Command-Line Arguments

| Argument  | Description | Default Value |
| ------------- | ------------- | ------------- |
| --domain     | Target GitLab instance URL  | https://c40b-88-222-161-135.ngrok-free.app |
| --file_name     | Payload file  | lfs_payload_3mb.json |
| --threads     | Total number of threads | 333 |
| --delay     | Limits the creation of new threads - 1 is 1 RPS, 0.5 is 2RPS, etc.  | 1 |

## Explanation

The /info/lfs/objects/batch endpoint accepts and renders unlimited JSON input. In the backend, it performs multiple resource-heavy operations, which would be fine if the input was under 1KB.

### Impact

Auto-scaling under attack can cause a cost spike, potentially breaching budget thresholds or credit limits.

If there's no auto-scaling and instance is default, recommended 8vCPU and 16GB ram:

In Linux, an OOM (Out-of-Memory) crash is technically referred to as an "OOM Killer event" or "OOM-induced system termination." In POC video, it crashes in the last 20 seconds.

![Cloud Provider Response](images/cloud_provider_response.png)

**Attack Vector (AV:N)** - Attacker can exploit this remotely.

**Attack Complexity (AC:L)** - Attack uses a very simple python script.

**Privileges Required (PR:N)** - The endpoint is unauthenticated.

**User Interaction (UI:N)** - There's no user interaction required.

**Scope (S:C)** - Changed. Affects VM, which is above Gitlab application and also affects cloud hosting account if auto-scaling is enabled.

**Integrity Impact (I:N)** - None. Might be low if temporary data is lost during VM crash.

**Availability Impact (A:H)** - High. Instance crashes completely, unavailable for all users.

From https://gitlab-com.gitlab.io/gl-security/product-security/appsec/cvss-calculator/

`When evaluating Availability impacts for DoS that require sustained traffic, use the 1k Reference Architecture. The number of requests must be fewer than the "test request per seconds rates" and cause 10+ seconds of user-perceivable unavailability to rate the impact as A:H.`

This attack used only 1RPS which eventually caused an OOM crash on 1k Reference Architecture instance.

### Theoretical Impact

1. Advanced Monitoring Blind Spots: Alert Overload as a Smokescreen for Data Exfiltration

DoS attacks are very noisy by nature—crashing services, flooding logs, and triggering alert storms. But that chaos can work in the attacker's favor. By overwhelming observability tools like Prometheus or Datadog with garbage metrics and cardinality explosions, an attacker can distract responders and degrade monitoring fidelity.

A DoS on GitLab instance, for example, might not be the end goal—just the distraction. While teams scramble to stabilize GitLab, the attacker quietly hits a more valuable target elsewhere: cloud buckets, internal APIs, or CI-linked infrastructure.

2. Cloud Provider Blacklisting/Suspension

The attack causes 100%+ CPU usage over extended period of time.
Providers like DigitalOcean, AWS, etc. use heuristic models to flag "suspicious" resource consumption. Legitimate causes (e.g., DDoS attacks, unoptimized code, or intensive computations) might be **mislabeled as abusive**, leading to temporary account suspension.

Cryptojacking and Uncontrolled Resource Consumption are very similar in a way that they both use up computational resources and can result in massive financial damages, budget limit based account locks or even suspensions.

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

## Company Information

GitLab is a web-based DevOps platform that provides a complete CI/CD (Continuous Integration/Continuous Delivery) pipeline, allowing developers to plan, develop, test, and deploy code from a single application. It includes features for version control (using Git), issue tracking, code review, and more, streamlining the software development lifecycle.

Who uses GitLab:
GitLab is used by a wide range of organizations—from startups to large enterprises—for managing source code and automating development workflows. Notable large companies and organizations that use GitLab include:

-Goldman Sachs
-Siemens
-NVIDIA
-T-Mobile
-NASA

GitLab is popular among teams that value open-source solutions, integrated DevOps tools, and on-premise deployment options for security and compliance.

Various branches and agencies within the U.S. Department of Defense (DoD) have adopted GitLab, particularly for secure, self-hosted DevSecOps environments. GitLab’s support for on-premise deployments, security features, and compliance tools make it well-suited for defense and government use, where data sensitivity and operational control are critical.

For example:

-Platform One, a DoD DevSecOps initiative, uses GitLab as part of its toolchain to modernize software development across military applications.

-GitLab has achieved FedRAMP authorization, making it compliant with federal security requirements for cloud services.

## Affected Websites

Shodan query: http.title:"GitLab"

Returns more than 50 thousand results.

![Shodan](images/shodan_gitlab_self_hosted.PNG)

## ⚠️ Legal Disclaimer  
This Proof-of-Concept (PoC) is provided **for educational purposes only**.  

- **Authorized Use Only**: Test only on systems you own or have explicit permission to assess.  
- **No Liability**: The author is not responsible for misuse or damages caused by this tool.  
- **Ethical Responsibility**: Do not use this tool to violate laws or exploit systems without consent.  

By using this software, you agree to these terms. 
